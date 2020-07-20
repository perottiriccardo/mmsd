# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
import salabim as sim
import numpy as np
import configparser

class PatientGenerator(sim.Component):
    def process(self):
        with MongoDB() as mongo:
            while True:
                for patient in mongo.query("PatientTrace", query={'relative_first_interaction_day': env.now()}, projection={'Pac_Unif_Cod': 1, 'appointments': 1}):
                    Patient(id=patient['Pac_Unif_Cod'], appointments=patient['appointments'])

                yield self.hold(1)

class Patient(sim.Component):
    def setup(self, id, appointments):
        self.id = id
        self.appointments = appointments

    def process(self):
        for i in range(len(self.appointments)):
            Appointment(pateintId=self.id, visitDay=self.appointments[i]['Visit day'], relativeVisitDay=self.appointments[i]['relative_visit_day'])

            if(i < len(self.appointments)-1):
                yield self.hold(self.appointments[i+1]['relative_waiting_list_entry_date'] - env.now())

class Appointment(sim.Component):
    def setup(self, pateintId, visitDay, relativeVisitDay):
        self.pateintId = pateintId
        self.visitDay = visitDay
        self.relativeVisitDay = relativeVisitDay

    def process(self):
        self.enter_sorted(appointmentsList, self.visitDay)

        if slot.ispassive():
            slot.activate()

        print(f"Appointment schedule -> Patient: {self.pateintId}")
        yield self.passivate()
        print(f"Appointment complete -> Patient: {self.pateintId}")

class AppointmentSlotExecute(sim.Component):
    def process(self):
        while True:
            while not appointmentsList:
                yield self.passivate()

            while appointmentsList.head().relativeVisitDay > env.now():
                yield self.hold(1)

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