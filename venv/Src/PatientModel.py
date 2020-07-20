# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
import salabim as sim
import numpy as np
import configparser

#Generatore di pazienti
class PatientGenerator(sim.Component):
    def process(self):
        with MongoDB() as mongo:
            while True:
                print(f"Day: {env.now()}")
                #Vengono selezionati i pazienti dal DB che hanno interagito per la prima volta con il sistema al giorno corrente
                for patient in mongo.query("PatientTrace", query={'relative_first_interaction_day': env.now()}, projection={'Pac_Unif_Cod': 1, 'appointments': 1}):
                    # Il paziente viene creato con il suo ID e i suoi appuntamenti
                    Patient(id=patient['Pac_Unif_Cod'], appointments=patient['appointments'])
                yield self.hold(1) #Rischedulazione del generatore ogni giorno (unità di tempo del sistema)

class Patient(sim.Component):
    def setup(self, id, appointments):
        self.id = id
        self.appointments = appointments

    def process(self):
        print(f"New patient: {self.id}")

        for i in range(len(self.appointments)):
            #Viene creato un appuntamento nel sistema
            Appointment(nAppointment=i+1, pateintId=self.id, visitDay=self.appointments[i]['Visit day'], relativeVisitDay=self.appointments[i]['relative_visit_day'])

            if(i < len(self.appointments)-1):
                #Il paziente attende la data di waiting list del successivo appuntamento per creare il nuovo appuntamento
                yield self.hold(self.appointments[i+1]['relative_waiting_list_entry_date'] - env.now())

class Appointment(sim.Component):
    def setup(self, nAppointment, pateintId, visitDay, relativeVisitDay):
        self.nAppointment = nAppointment
        self.pateintId = pateintId
        self.visitDay = visitDay
        self.relativeVisitDay = relativeVisitDay

    def process(self):
        #Viene inserito l'appuntamento nella coda, in ordine di data di visita
        self.enter_sorted(appointmentsList, self.visitDay)

        if slot.ispassive():
            slot.activate()

        print(f"Appointment schedule {self.nAppointment} -> Patient: {self.pateintId}")
        yield self.passivate()
        print(f"Appointment complete {self.nAppointment} -> Patient: {self.pateintId}")

class AppointmentSlotExecute(sim.Component):
    def process(self):
        while True:
            while not appointmentsList:
                yield self.passivate()

            #A seconda dello scheduling della testa della coda, si attendono i giorni necessari
            while appointmentsList.head().relativeVisitDay > env.now():
                yield self.hold(1)

            #L'appuntamento è estratto dalla coda e viene processato e poi completato
            appointment = appointmentsList.pop()

            yield self.hold(env.minutes(30))
            appointment.activate()



config = configparser.ConfigParser()
config.read('ConfigFile.properties')

env = sim.Environment(trace=False, time_unit='days')

PatientGenerator()
slot = AppointmentSlotExecute()
appointmentsList = sim.Queue("appointments")

env.run(till=100)