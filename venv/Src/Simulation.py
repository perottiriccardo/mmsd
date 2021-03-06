# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
import salabim as sim, configparser, math, image, time, numpy as np

class HospitalBook(sim.Component):
    def process(self):
        while True:
            while len(patientBookQueue) == 0:
                yield self.passivate()

            # Prendo il paziente che deve prenotare e creo l'appuntamento con i dati dello stesso (currentIndex mi dice il numero dell'appuntamnto del paziente che stiamo creando)
            patient = patientBookQueue.pop()
            appointment = Appointment(nAppointment=patient.currentIndex + 1, patientId=patient.id,
                        info=patient.appointments[patient.currentIndex])

            if int(config['Params']['stochasticScenary']):
                if np.random.choice(2, 1, p=[1 - float(config['Probabilities']['reminderDone']), config['Probabilities']['reminderDone']]) == 0:
                    self._defineVisitStatus(appointment, reminderNoneVisitStatus)
                else:
                    reminderSampled = np.random.choice(4, 1, p=[float(reminderType[0]),
                                                                float(reminderType[1]),
                                                                float(reminderType[2]),
                                                                float(reminderType[3])])
                    if reminderSampled == 0:
                        appointment.info["Appointment remainder"] = "Phone"
                    elif reminderSampled == 1:
                        appointment.info["Appointment remainder"] = "SMS"
                    elif reminderSampled == 2:
                        appointment.info["Appointment remainder"] = "Phone+SMS"
                    elif reminderSampled == 3:
                        appointment.info["Appointment remainder"] = "Other"

                    Reminder(appointment=appointment)
                    self._defineVisitStatus(appointment, reminderDoneVisitStatus)
            else:
                # Creo il reminder se esiste e creo la cancellazione dell'ospedale se necessaria
                if appointment.info['Appointment remainder'] != "None":
                    Reminder(appointment=appointment)

            # Se l'appuntamento non è stato cancellato lo inserisco nella coda di appuntamenti da schedulare e attivo HospitalSchedule
            if appointment.info["Visit status"] != "Cancelled HS" and appointment.info[
                "Visit status"] != "Cancelled Pat":
                appointment.enter_sorted(appointmentScheduleQueue,
                                         patient.appointments[patient.currentIndex]['relative_visit_day'])

                if hospitalSchedule.ispassive():
                    hospitalSchedule.activate()

            if appointment.info["Visit status"] == "Cancelled HS":
                CancelAppointment(appointment = appointment)

            # Riattivo il paziente che ha prenotato per permettergli di prenotare gli appuntamenti successivi e continuo con i restanti pazienti
            patient.activate()

    def _defineVisitStatus(self, appointment, visitStatusProbabilities):
        visitStatusSampled = np.random.choice(4, 1, p=[float(visitStatusProbabilities[0]), float(visitStatusProbabilities[1]),
                                                 float(visitStatusProbabilities[2]), float(visitStatusProbabilities[3])])
        if visitStatusSampled == 0:
            appointment.info["Visit status"] = "Done"
        elif visitStatusSampled == 1:
            appointment.info["Visit status"] = "NoShowUp"
        elif visitStatusSampled == 2:
            appointment.info["Visit status"] = "Cancelled Pat"
        elif visitStatusSampled == 3:
            appointment.info["Visit status"] = "Cancelled HS"

class HospitalSchedule(sim.Component):
    def process(self):
        while True:
            while len(appointmentScheduleQueue) == 0:
                yield self.passivate()

            # Aspetto il giorno successivo se ho schedulato tutti gli appuntamenti della giornata (+0.0001 per permettere anche agli appuntamenti di mezzanotte di essere messi nella coda di priorità (da HospitalBook) prima di essere schedulati)
            while int(appointmentScheduleQueue.head().info['relative_visit_day']) - int(env.now()) > 0:
                yield self.hold(math.floor(env.now()+1) - env.now() + 0.0001)

            # Prendo il primo appuntamento dalla coda di priorità e attendo l'ora di scheduling per attivarlo. Poi continuo con gli appuntamenti successivi che saranno temporalmente successivi a questo preso in considerazione
            appointment = appointmentScheduleQueue.pop()
            yield self.hold(appointment.info['relative_visit_day'] - env.now() + 0.0001)
            appointment.activate()

class Reminder(sim.Component):
    def setup(self, appointment):
        self.appointment = appointment

    def process(self):
        global reminders

        # Attendo 2 giorni prima dell'appuntamento per mandare il reminder, se non possibile attendo 1 giorno prima, altrimenti lo mando l'ora e il giorno dell'appuntamento
        if int(self.appointment.info['relative_visit_day'] - env.now()) > 2:
            yield self.hold(int(self.appointment.info['relative_visit_day'] - env.now()) - 2)
        elif int(self.appointment.info['relative_visit_day'] - env.now()) > 1:
            yield self.hold(int(self.appointment.info['relative_visit_day'] - env.now()) - 1)
        else:
            yield self.hold(int(self.appointment.info['relative_visit_day'] - env.now()))

        # Setto il reminder nell'appuntamento
        self.appointment.reminded = self.appointment.info["Appointment remainder"]

        if validate: reminders[self.appointment.reminded] += 1
        if trace: print(f"Reminded {self.appointment.patientId}")

class CancelAppointment(sim.Component):
    def setup(self, appointment):
        self.appointment = appointment

    def process(self):
        # Attendo un tempo casuale tra oggi e il giorno dell'appuntamento per cancellarlo
        yield self.hold(sim.Uniform(0, int(self.appointment.info['relative_visit_day'] - env.now())))
        self.appointment.activate()

class PatientGenerator(sim.Component):
    def process(self):
        with MongoDB() as mongo:
            while True:
                # Vengono selezionati i pazienti dal DB che hanno interagito per la prima volta con il sistema al giorno corrente
                for patient in mongo.query("PatientTrace", query={'relative_first_interaction_day': env.now()}, projection={'Pac_Unif_Cod': 1, 'appointments': 1}):
                    # Il paziente viene creato con il suo ID e i suoi appuntamenti
                    Patient(id=patient['Pac_Unif_Cod'], appointments=patient['appointments'])

                yield self.hold(1) # Rischedulazione del generatore ogni giorno (unità di tempo del sistema)

class Patient(sim.Component):
    def setup(self, id, appointments):
        self.id = id
        self.appointments = appointments

    def process(self):
        if trace: print(f"New patient: {self.id}")

        for i in range(len(self.appointments)):
            # Aggiungo il paziente alla lista di pazienti che vogliono prenotare un appuntamento oggi stesso e setto l'indice dell'appunatmento
            self.enter(patientBookQueue)
            self.currentIndex = i

            # Attivo la HospitalBook per permettere la prenotazione se non attivo
            if hospitalBook.ispassive():
                hospitalBook.activate()

            # Attendo che HospitalBook risvegli il paziente una volta effettuata la prenotazione
            yield self.passivate()

            # Se il paziente deve prenotare altri appuntamenti attende la data di waiting list del successivo per crearlo
            if(i < len(self.appointments)-1):
                yield self.hold(self.appointments[i+1]['relative_waiting_list_entry_date'] - env.now())

class Appointment(sim.Component):
    def setup(self, nAppointment, patientId, info):
        self.startWaitingDay = env.now()
        self.nAppointment = nAppointment
        self.patientId = patientId
        self.info = info
        self.reminded = None

    def process(self):
        global nAppointmentsDict, totDaysInWaitingListDict, visitStatus, patientAppointmentsDayDict, patientAppointmentsStatusDict, patientAppointmentsWaitingDaysDict

        if trace: print(f"Appointment schedule {self.nAppointment} -> Patient: {self.patientId}")

        if self.info['Visit status'] == 'Cancelled Pat':
            # Attendo un valore tra 0 e i giorni che mancano alla visita per cancellare l'appuntamento
            yield self.hold(sim.Uniform(0, int(self.info['relative_visit_day'] - env.now())))

            if trace: print(f"Appointment cancelled from Pat {self.nAppointment} -> Patient: {self.patientId}")
        elif self.info['Visit status'] == 'Cancelled HS':
            yield self.passivate()

            if trace: print(f"Appointment cancelled from HS {self.nAppointment} -> Patient: {self.patientId}")
        elif self.info['Visit status'] == 'NoShowUp':
            if np.random.choice(2, 1, p=[1-float(config['Probabilities']['noShowUpNotice']), config['Probabilities']['noShowUpNotice']]) == 0:
                # Attendo fino al giorno dell'appuntamento
                yield self.passivate()

                if str(env.now())[-5:] == ".0001":
                    yield self.hold(sim.Uniform(8, 18, "hours"))

                # Richiedo una risorsa slot
                yield self.request(slots)

                if trace: print(f"Appointment no show up {self.nAppointment} -> Patient: {self.patientId}")

                # Tengo lo slot occupato per 15 minuti
                yield self.hold(env.minutes(timeSlot))
                self.release(slots)
            else:
                yield self.hold(sim.Triangular(0, int(self.info['relative_visit_day'] - env.now()), math.floor(int(self.info['relative_visit_day'] - env.now()))*90/100))

                self.leave(appointmentScheduleQueue)
                self.info['Visit status'] = 'Cancelled Pat (noShowUp)'

                ReplaceAppointment(appointment=self)
        elif self.info['Visit status'] == 'Done':
            # Attendo fino al giorno dell'appuntamento
            yield self.passivate()

            if str(env.now())[-5:] == ".0001":
                yield self.hold(sim.Uniform(8, 18, "hours"))

            # Richiedo una risorsa slot
            yield self.request(slots)
            # Richiedo una risorsa dottore
            yield self.request(doctors)
            # Quando il dottore è disponibile faccio la visita di 15 minuti
            yield self.hold(env.minutes(timeSlot))

            # Rilascio la risorsa dottore
            self.release(doctors)
            self.release(slots)

            if trace: print(f"Appointment done {self.nAppointment} -> Patient: {self.patientId}")

        if validate:
            if self.info['Visit status'] == 'Cancelled Pat (noShowUp)':
                self.info['Visit status'] = 'Cancelled Pat'
                nAppointmentsDict['TriedToReplaced'] += 1

            if self.patientId not in patientAppointmentsStatusDict:
                patientAppointmentsStatusDict[self.patientId] = {"NoShowUp": 0, "Done": 0, "Cancelled Pat": 0, "Cancelled HS": 0}

            nAppointmentsDict['Tot'] += 1
            visitStatus[self.info['Visit status']] += 1
            patientAppointmentsStatusDict[self.patientId][self.info['Visit status']] += 1

            if self.info['Visit status'] == 'Done' or self.info['Visit status'] == 'NoShowUp':
                if self.patientId not in patientAppointmentsDayDict:
                    patientAppointmentsDayDict[self.patientId] = []
                patientAppointmentsDayDict[self.patientId].append(int(env.now()))

                if self.patientId not in patientAppointmentsWaitingDaysDict:
                    patientAppointmentsWaitingDaysDict[self.patientId] = 0
                patientAppointmentsWaitingDaysDict[self.patientId] += int(env.now()) - self.startWaitingDay

                totDaysInWaitingListDict['Tot'] += int(env.now())-self.startWaitingDay

                if self.info['Character of visit'] == 'Preferential' or self.info['Character of visit'] == 'Ordinary':
                    totDaysInWaitingListDict[self.info['Character of visit']] += int(env.now()) - self.startWaitingDay
                    nAppointmentsDict[self.info['Character of visit']] += 1

                    if self.info['Visit status'] == 'Done':
                        totDaysInWaitingListDict['OnlyDone' + self.info['Character of visit']] += int(env.now()) - self.startWaitingDay
                        nAppointmentsDict['OnlyDone' + self.info['Character of visit']] += 1

                if self.info['Visit type'] == 'First' or self.info['Visit type'] == 'Revision':
                    totDaysInWaitingListDict[self.info['Visit type']] += int(env.now()) - self.startWaitingDay
                    nAppointmentsDict[self.info['Visit type']] += 1

                    if self.info['Visit status'] == 'Done':
                        totDaysInWaitingListDict['OnlyDone' + self.info['Visit type']] += int(env.now()) - self.startWaitingDay
                        nAppointmentsDict['OnlyDone' + self.info['Visit type']] += 1

                if int(env.now()) != int(self.info['relative_visit_day']):
                    nAppointmentsDict['Wrong'] += 1

class ReplaceAppointment(sim.Component):
    def setup(self, appointment):
        self.appointment = appointment

    def process(self):
        global nAppointmentsDict

        for appointment in appointmentScheduleQueue:
            if 1 <= appointment.info['relative_visit_day'] - self.appointment.info['relative_visit_day'] <= 3 and \
                    appointment.info['Visit status'] == 'Done' and \
                    appointment.info['Visit type'] in substituteVisitTypes and \
                    appointment.info['Character of visit'] in substituteCharacterOfVisit and \
                    np.random.choice(2, 1, p=[1-float(config['Probabilities']["substituteCharacterOfVisit" + appointment.info['Character of visit']]), float(config['Probabilities']["substituteCharacterOfVisit" + appointment.info['Character of visit']])]) == 1:
                appointment.leave(appointmentScheduleQueue)
                appointment.info['relative_visit_day'] = self.appointment.info['relative_visit_day']
                appointment.enter_sorted(appointmentScheduleQueue, appointment.info['relative_visit_day'])
                return

            if appointment.info['relative_visit_day'] - self.appointment.info['relative_visit_day'] >3:
                if validate: nAppointmentsDict['NotReplaced'] += 1
                return

        if validate: nAppointmentsDict['NotReplaced'] += 1

class DepartmentCapacity(sim.Component):
    def process(self):
        while True:
            if trace: print(round(env.now()))
            print(round(env.now()))

            # Gestisce la capacità dei dottori in base agli appuntamenti giornalieri previsti al mattino (8:00 - 14:30) e al pomeriggio (14:30 - 22:00)
            slots.set_capacity(0)
            doctors.set_capacity(0)
            yield self.hold(env.hours(8))

            capacity = int(doctorPerDayMorning[int(env.now())])
            slots.set_capacity(capacity)
            doctors.set_capacity(capacity)
            yield self.hold(env.hours(6))

            capacity = int(doctorPerDayAfternoon[int(env.now())])
            slots.set_capacity(capacity)
            doctors.set_capacity(capacity)
            yield self.hold(env.hours(8))

            slots.set_capacity(0)
            doctors.set_capacity(0)
            yield self.hold(env.hours(2))


start_time = time.time()

config = configparser.ConfigParser()
config.read('ConfigFile.properties')

doctorPerDayMorning = config['DoctorPerDay']['morning'].split(",")
doctorPerDayAfternoon = config['DoctorPerDay']['afternoon'].split(",")
substituteCharacterOfVisit = config['Params']['substituteCharacterOfVisit'].split(",")
substituteVisitTypes = config['Params']['substituteVisitTypes'].split(",")

if int(config['Params']['stochasticScenary']):
    reminderDoneVisitStatus = config['Probabilities']['reminderDoneVisitStatus'].split(",")
    reminderNoneVisitStatus = config['Probabilities']['reminderNoneVisitStatus'].split(",")
    reminderType = config['Probabilities']['reminderType'].split(",")

# Variabili per la validazione
visitStatus = { "NoShowUp": 0, "Done": 0, "Cancelled Pat": 0, "Cancelled HS": 0}
reminders = { "SMS": 0, "Phone+SMS": 0, "Phone": 0, "Other": 0}
nAppointmentsDict = {"Tot": 0, "Wrong": 0, "TriedToReplaced": 0, "NotReplaced": 0, "Ordinary": 0, "Preferential": 0, "OnlyDoneOrdinary": 0, "OnlyDonePreferential": 0, "First": 0, "Revision": 0, "OnlyDoneFirst": 0, "OnlyDoneRevision": 0}
totDaysInWaitingListDict = {"Tot": 0, "Ordinary": 0, "Preferential": 0, "OnlyDoneOrdinary": 0, "OnlyDonePreferential": 0, "First": 0, "Revision": 0, "OnlyDoneFirst": 0, "OnlyDoneRevision": 0}
patientAppointmentsDayDict = {}
patientAppointmentsWaitingDaysDict = {}
patientAppointmentsStatusDict = {}

# Variabili per avere maggiori informazioni
validate = True
trace = False

timeSlot = 15
env = sim.Environment(trace=False, time_unit='days')
env.animate(True)

patientBookQueue = sim.Queue("patientBookQueue")
appointmentScheduleQueue = sim.Queue("appointmentScheduleQueue")

PatientGenerator()
hospitalBook = HospitalBook()
hospitalSchedule = HospitalSchedule()



# Creata la risorsa slot con una capacità variabile
slots = sim.Resource('Slot')
# Creata la risorsa dottore con una capacità variabile
doctors = sim.Resource('Doctor')
DepartmentCapacity()

# env.modelname("Patients not show up simulation")
# env.background_color("20%gray")
env.speed(300)

# sim.AnimateQueue(slots.requesters(), x=30, y=650, title='Requester queue', direction='e', id='blue')
# sim.AnimateQueue(slots.claimers(), x=30, y=580, title='Claimers queue', direction='e', id='blue')
# sim.AnimateMonitor(slots.available_quantity, x=10, y=480, width=950, height=50, horizontal_scale=600, vertical_scale=8)
# sim.AnimateMonitor(slots.claimed_quantity, x=10, y=400, width=950, height=50, horizontal_scale=600, vertical_scale=8)
# sim.AnimateMonitor(slots.occupancy, x=10, y=320, width=950, height=50, horizontal_scale=600, vertical_scale=8)
#
# sim.AnimateText(text=lambda: slots.print_info(as_str=True), x=10, y=270,
#                 text_anchor='nw', font='narrow', fontsize=14)

env.run(till=2191)

out_file = open("../Resources/results_sub_" + config["Probabilities"]["noShowUpNotice"] + ".txt", "w")

elapsed_time = time.time() - start_time
out_file.write(f"Execution time: {elapsed_time}")

slots.print_statistics()
doctors.print_statistics()

if validate:
    out_file.write(f"\nAppointments: {nAppointmentsDict['Tot']}")
    out_file.write(f"\nAppointments tried to replaced (no show up): {nAppointmentsDict['TriedToReplaced']}")
    out_file.write(f"\nAppointments not found substitute: {nAppointmentsDict['NotReplaced']}")
    out_file.write(f"\nAppointments execute in wrong day (without cancelled): {nAppointmentsDict['Wrong']}")

    # Validazione giorni di attesa medi degli appuntamenti
    out_file.write(f"\n\nMean days in waiting list (without cancelled): {totDaysInWaitingListDict['Tot']/sum([dict['Done'] + dict['NoShowUp'] for dict in patientAppointmentsStatusDict.values()])}")
    out_file.write(f"\nMean days ordinary in waiting list (without cancelled): {totDaysInWaitingListDict['Ordinary']/nAppointmentsDict['Ordinary']}")
    out_file.write(f"\nMean days ordinary in waiting list (without cancelled and no show up): {totDaysInWaitingListDict['OnlyDoneOrdinary']/nAppointmentsDict['OnlyDoneOrdinary']}")
    out_file.write(f"\nMean days preferential in waiting list (without cancelled): {totDaysInWaitingListDict['Preferential']/nAppointmentsDict['Preferential']}")
    out_file.write(f"\nMean days preferential in waiting list (without cancelled and no show up): {totDaysInWaitingListDict['OnlyDonePreferential']/nAppointmentsDict['OnlyDonePreferential']}")
    out_file.write(f"\nMean days first in waiting list (without cancelled): {totDaysInWaitingListDict['First']/nAppointmentsDict['First']}")
    out_file.write(f"\nMean days first in waiting list (without cancelled and no show up): {totDaysInWaitingListDict['OnlyDoneFirst']/nAppointmentsDict['OnlyDoneFirst']}")
    out_file.write(f"\nMean days revision in waiting list (without cancelled): {totDaysInWaitingListDict['Revision']/nAppointmentsDict['Revision']}")
    out_file.write(f"\nMean days revision in waiting list (without cancelled and no show up): {totDaysInWaitingListDict['OnlyDoneRevision']/nAppointmentsDict['OnlyDoneRevision']}")

    # Validazione statistiche generali sullo status degli appuntamenti
    out_file.write(f"\n\nNoShowUp: {visitStatus['NoShowUp']} -> {visitStatus['NoShowUp']/nAppointmentsDict['Tot']*100}")
    out_file.write(f"\nDone: {visitStatus['Done']} -> {visitStatus['Done']/nAppointmentsDict['Tot']*100}")
    out_file.write(f"\nCancelled Pat: {visitStatus['Cancelled Pat']} -> {visitStatus['Cancelled Pat']/nAppointmentsDict['Tot']*100}")
    out_file.write(f"\nCancelled HS: {visitStatus['Cancelled HS']} -> {visitStatus['Cancelled HS']/nAppointmentsDict['Tot']*100}")

    # Validazione statistiche genearli sui reminders degli appuntamenti
    out_file.write(f"\n\nSMS: {reminders['SMS']} -> {reminders['SMS']/nAppointmentsDict['Tot']*100}")
    out_file.write(f"\nPhone+SMS: {reminders['Phone+SMS']} -> {reminders['Phone+SMS']/nAppointmentsDict['Tot']*100}")
    out_file.write(f"\nPhone: {reminders['Phone']} -> {reminders['Phone']/nAppointmentsDict['Tot']*100}")
    out_file.write(f"\nOther: {reminders['Other']} -> {reminders['Other']/nAppointmentsDict['Tot']*100}")
    out_file.write(f"\nNone: {nAppointmentsDict['Tot'] - (reminders['SMS']+reminders['Phone+SMS']+reminders['Phone']+reminders['Other'])} -> {(nAppointmentsDict['Tot'] - (reminders['SMS']+reminders['Phone+SMS']+reminders['Phone']+reminders['Other']))/nAppointmentsDict['Tot']*100}\n")

    if not int(config['Params']['stochasticScenary']):
        with MongoDB() as mongo:
            for patientStatistics in mongo.query("PatientStatistic"):
                # Validazione status degli appuntamenti per ogni paziente
                if patientStatistics['pac_unif_cod'] not in patientAppointmentsStatusDict:
                   if patientStatistics['visit_status_appointments']['done'] != 0 or \
                    patientStatistics['visit_status_appointments']['no_show_up'] != 0 or \
                    patientStatistics['visit_status_appointments']['cancelled'] != 0:
                       out_file.write(f"\n{patientStatistics['pac_unif_cod']} -> Wrong appointments status")
                elif patientStatistics['visit_status_appointments']['done'] != patientAppointmentsStatusDict[patientStatistics['pac_unif_cod']]['Done'] or \
                    patientStatistics['visit_status_appointments']['no_show_up'] != patientAppointmentsStatusDict[patientStatistics['pac_unif_cod']]['NoShowUp'] or \
                    patientStatistics['visit_status_appointments']['cancelled'] != patientAppointmentsStatusDict[patientStatistics['pac_unif_cod']]['Cancelled Pat'] + patientAppointmentsStatusDict[patientStatistics['pac_unif_cod']]['Cancelled HS']:
                    out_file.write(f"\n{patientStatistics['pac_unif_cod']} -> Wrong appointments status")

                # Validazione del tempo medio in waiting list per ogni paziente
                if patientStatistics['pac_unif_cod'] in patientAppointmentsWaitingDaysDict:
                    if round(patientStatistics['mean_days_in_waiting_list_without_cancelled'], 3) != round(patientAppointmentsWaitingDaysDict[patientStatistics['pac_unif_cod']]/(patientAppointmentsStatusDict[patientStatistics['pac_unif_cod']]['Done'] + patientAppointmentsStatusDict[patientStatistics['pac_unif_cod']]['NoShowUp']), 3):
                        out_file.write(f"\n{patientStatistics['pac_unif_cod']} -> Different mean time in waiting list -> real:"
                                       f" {round(patientStatistics['mean_days_in_waiting_list_without_cancelled'], 3)}, simulation:"
                                       f" {round(patientAppointmentsWaitingDaysDict[patientStatistics['pac_unif_cod']]/(patientAppointmentsStatusDict[patientStatistics['pac_unif_cod']]['Done'] + patientAppointmentsStatusDict[patientStatistics['pac_unif_cod']]['NoShowUp']), 3)}")

                # Validazione del numero di intervalli tra appuntamenti NoShowUp e Done per ogni paziente
                if patientStatistics['pac_unif_cod'] not in patientAppointmentsDayDict:
                    if len(patientStatistics['elapsed_time_between_appointments_without_cancelled']) > 0:
                        out_file.write(f"\n{patientStatistics['pac_unif_cod']} -> Different number of appointments")
                        continue
                elif len(patientStatistics['elapsed_time_between_appointments_without_cancelled']) != len(patientAppointmentsDayDict[patientStatistics['pac_unif_cod']])-1:
                    out_file.write(f"\n{patientStatistics['pac_unif_cod']} -> Different number of appointments")
                    continue

                # Validazione degli intervalli tra appuntamenti NoShowUp e Done per ogni paziente
                for i in range(len(patientStatistics['elapsed_time_between_appointments_without_cancelled'])):
                    if (patientAppointmentsDayDict[patientStatistics['pac_unif_cod']][i+1] - patientAppointmentsDayDict[patientStatistics['pac_unif_cod']][i]) != patientStatistics['elapsed_time_between_appointments_without_cancelled'][i]['elapsed_time']:
                        out_file.write(f"\n{patientStatistics['pac_unif_cod']} "
                              f"-> {i} -- DIFF: {patientAppointmentsDayDict[patientStatistics['pac_unif_cod']][i+1] - patientAppointmentsDayDict[patientStatistics['pac_unif_cod']][i] - patientStatistics['elapsed_time_between_appointments_without_cancelled'][i]['elapsed_time']}")

out_file.close()
