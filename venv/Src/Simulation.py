# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
import salabim as sim
import configparser
import math
import image

class Hospital(sim.Component):
    def process(self):
        while True:
            while len(patientBookQueue) == 0:
                yield self.passivate()
            self.patient = patientBookQueue.pop()

            appointment = Appointment(nAppointment=self.patient.currentIndex + 1,
                        patientId=self.patient.id,
                        info=self.patient.appointments[self.patient.currentIndex])
            if appointment.info['Appointment remainder'] != "None":
                Reminder(appointment=appointment)
            if appointment.info["Visit status"] == "Cancelled HS":
                CancelAppointment(appointment = appointment)

            self.patient.activate()

class Reminder(sim.Component):
    def setup(self, appointment):
        self.appointment = appointment

    def process(self):
        global reminders
        if int(self.appointment.info['relative_visit_day'] - env.now()) > 2:
            yield self.hold(int(self.appointment.info['relative_visit_day'] - env.now()) - 2)
        else:
            yield self.hold(int(self.appointment.info['relative_visit_day'] - env.now()))
        self.appointment.reminded = self.appointment.info["Appointment remainder"]

        reminders[self.appointment.reminded] += 1
        # print(f"Reminded {self.appointment.patientId}")

class CancelAppointment(sim.Component):
    def setup(self, appointment):
        self.appointment = appointment

    def process(self):
        yield self.hold(sim.Uniform(0, int(self.appointment.info['relative_visit_day'] - env.now())))
        self.appointment.activate()

# Generatore di pazienti
class PatientGenerator(sim.Component):
    def process(self):
        with MongoDB() as mongo:
            while True:
                #print(f"Day: {env.now()}")
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
        #print(f"New patient: {self.id}")

        for i in range(len(self.appointments)):

            # Viene creato un appuntamento nel sistema
            self.enter(patientBookQueue)
            self.currentIndex = i

            if hospital.ispassive():
                hospital.activate()

            yield self.passivate()

            if(i < len(self.appointments)-1):
                # Il paziente attende la data di waiting list del successivo appuntamento per creare il nuovo appuntamento
                yield self.hold(self.appointments[i+1]['relative_waiting_list_entry_date'] - env.now())

class Appointment(sim.Component):
    def setup(self, nAppointment, patientId, info):
        self.nAppointment = nAppointment
        self.patientId = patientId
        self.info = info
        self.reminded = None

    def process(self):
        global nAppointments, visitStatus, patientDict

        #print(f"Appointment schedule {self.nAppointment} -> Patient: {self.patientId}")
        nAppointments += 1

        if self.info['Visit status'] == 'Cancelled Pat':
            # Attendo un valore tra 0 e i giorni che mancano alla visita per cancellare l'appuntamento
            yield self.hold(sim.Uniform(0, int(self.info['relative_visit_day'] - env.now())))
            #print(f"Appointment cancelled from Pat {self.nAppointment} -> Patient: {self.patientId}")
            visitStatus[self.info['Visit status']] += 1
        elif self.info['Visit status'] == 'Cancelled HS':
            yield self.passivate()
            #print(f"Appointment cancelled from HS {self.nAppointment} -> Patient: {self.patientId}")
            visitStatus[self.info['Visit status']] += 1
        elif self.info['Visit status'] == 'NoShowUp' or self.info['Visit status'] == 'Done':
            # Attendo fino al giorno dell'appuntamento
            yield self.hold(self.info['relative_visit_day'] - env.now())

            if str(env.now())[-2:] == ".0":
                yield self.hold(sim.Uniform(8, 18, "hours"))

            # Richiedo una risorsa slot
            yield self.request(slots)

            if self.info['Visit status'] == 'NoShowUp':
                #print(f"Appointment no show up {self.nAppointment} -> Patient: {self.patientId}")

                # Tengo lo slot occupato per 15 minuti
                yield self.hold(env.minutes(timeSlot))
                self.release(slots)
                visitStatus[self.info['Visit status']] +=1
            else:
                # Richiedo una risorsa dottore
                yield self.request(doctors)
                # Quando il dottore è disponibile faccio la visita di 15 minuti
                yield self.hold(env.minutes(timeSlot))

                # Rilascio la risorsa dottore
                self.release(doctors)
                self.release(slots)

                visitStatus[self.info['Visit status']] +=1

                #print(f"Appointment done {self.nAppointment} -> Patient: {self.patientId}")

            if self.patientId not in patientDict:
                patientDict[self.patientId] = []

            patientDict[self.patientId].append((int(env.now()), self.info['Visit status'][:1]))

class DepartmentCapacity(sim.Component):
    def process(self):
        while True:
            if round(env.now()) % 7 == 0 or round(env.now()) % 7 == 6:
                slots.set_capacity(0)
                doctors.set_capacity(0)
                yield self.hold(1)
            else:
                slots.set_capacity(0)
                doctors.set_capacity(0)
                yield self.hold(env.hours(8))

                slots.set_capacity(10)
                doctors.set_capacity(10)
                yield self.hold(env.hours(6.5))

                slots.set_capacity(4)
                doctors.set_capacity(4)
                yield self.hold(env.hours(7.5))

                slots.set_capacity(0)
                doctors.set_capacity(0)
                yield self.hold(env.hours(2))


visitStatus = { "NoShowUp" : 0, "Done" : 0, "Cancelled Pat" : 0, "Cancelled HS" : 0}
reminders = { "SMS" : 0, "Phone+SMS" : 0, "Phone": 0, "Other": 0}
nAppointments = 0
patientDict = {}

# config = configparser.ConfigParser()
# config.read('ConfigFile.properties')

timeSlot = 15
env = sim.Environment(trace=False, time_unit='days')
env.animate(True)

patientBookQueue = sim.Queue("patientBookQueue")
PatientGenerator()
hospital = Hospital()
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

env.run(till=2200)

#slots.print_statistics()
#doctors.print_statistics()

print(f"Appointments: {nAppointments}")
print(f"NoShowUp: {visitStatus['NoShowUp']/nAppointments*100}")
print(f"Done: {visitStatus['Done']/nAppointments*100}")
print(f"Cancelled Pat: {visitStatus['Cancelled Pat']/nAppointments*100}")
print(f"Cancelled HS: {visitStatus['Cancelled HS']/nAppointments*100}")

print(f"SMS: {reminders['SMS']/nAppointments*100}")
print(f"Phone+SMS: {reminders['Phone+SMS']/nAppointments*100}")
print(f"Phone: {reminders['Phone']/nAppointments*100}")
print(f"Other: {reminders['Other']/nAppointments*100}")
print(f"None: {(nAppointments - (reminders['SMS']+reminders['Phone+SMS']+reminders['Phone']+reminders['Other']))/nAppointments*100}")


with MongoDB() as mongo:
    for patientStatistics in mongo.query("PatientStatistic", projection={'pac_unif_cod': 1, 'elapsed_time_between_appointments_without_cancelled': 1}):
        for i in range(len(patientStatistics['elapsed_time_between_appointments_without_cancelled'])):
            if (patientDict[patientStatistics['pac_unif_cod']][i+1][0] - patientDict[patientStatistics['pac_unif_cod']][i][0]) != patientStatistics['elapsed_time_between_appointments_without_cancelled'][i]['elapsed_time']:
                print(f"{patientStatistics['pac_unif_cod']} "
                      f"{patientDict[patientStatistics['pac_unif_cod']][i][1]} - {patientDict[patientStatistics['pac_unif_cod']][i+1][1]}"
                      f"-> {i} -- DIFF: {patientDict[patientStatistics['pac_unif_cod']][i+1][0] - patientDict[patientStatistics['pac_unif_cod']][i][0] - patientStatistics['elapsed_time_between_appointments_without_cancelled'][i]['elapsed_time']}")