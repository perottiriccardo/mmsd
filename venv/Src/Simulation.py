# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
import salabim as sim
import numpy as np
import configparser
import math


# Generatore di pazienti
class PatientGenerator(sim.Component):
    def process(self):
        with MongoDB() as mongo:
            while True:
                print(f"Day: {env.now()}")
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
        print(f"New patient: {self.id}")

        for i in range(len(self.appointments)):
            # Viene creato un appuntamento nel sistema
            Appointment(nAppointment=i+1, pateintId=self.id, info=self.appointments[i])

            if(i < len(self.appointments)-1):
                # Il paziente attende la data di waiting list del successivo appuntamento per creare il nuovo appuntamento
                yield self.hold(self.appointments[i+1]['relative_waiting_list_entry_date'] - env.now())

class Appointment(sim.Component): # TODO Ora esatta dello slot? Es giorno 5.026
    def setup(self, nAppointment, pateintId, info):
        self.nAppointment = nAppointment
        self.pateintId = pateintId
        self.info = info

    def process(self):
        print(f"Appointment schedule {self.nAppointment} -> Patient: {self.pateintId}")

        if self.info['Visit status'] == 'Cancelled Pat' or self.info['Visit status'] == 'Cancelled HS':
            # Attendo un valore tra 0 e i giorni che mancano alla visita per cancellare l'appuntamento
            yield self.hold(sim.Uniform(0, self.info['relative_visit_day'] - env.now()))
            print(f"Appointment cancelled {self.nAppointment} -> Patient: {self.pateintId}")
        else:
            # Attendo fino al giorno dell'appuntamento
            yield self.hold(self.info['relative_visit_day'] - env.now())
            # Richiedo una risorsa slot
            yield self.request(slots)

            if self.info['Visit status'] == 'NoShowUp':
                print(f"Appointment no show up {self.nAppointment} -> Patient: {self.pateintId}")

                # Tengo lo slot occupato per 15 minuti
                yield self.hold(env.minutes(15))
                self.release(slots)
            else:
                # Richiedo una risorsa dottore
                yield self.request(doctors)
                # Quando il dottore è disponibile faccio la visita di 15 minuti
                yield self.hold(env.minutes(15)) # TODO random tra 10/15/20 minuti?

                # Rilascio la risorsa dottore
                self.release(doctors)
                self.release(slots)

                print(f"Appointment done {self.nAppointment} -> Patient: {self.pateintId}")


# config = configparser.ConfigParser()
# config.read('ConfigFile.properties')

env = sim.Environment(trace=False, time_unit='days')

PatientGenerator()
# Creata la risorsa slot con una capacità di 6
slots = sim.Resource('Slot', capacity=6)
# Creata la risorsa dottore con una capacità di 6
doctors = sim.Resource('Doctor', capacity=6)

env.run(till=500)

slots.print_statistics()
doctors.print_statistics()