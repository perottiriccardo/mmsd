import salabim as sim
import numpy as np

class PatientGenerator(sim.Component):
    def process(self):
        while True:
            Patient()
            yield self.hold(sim.Uniform(5, 15).sample())

class Patient(sim.Component):
    def process(self):
        self.enter(waitingListNonPrioritary) if np.random.choice(2, 1, p=[1, 0]) == 0 else self.enter(waitingListPrioritary)
        # TODO Inserire un timeout se appointmentslot è passivo e arriva un paziente in coda
        if slot.ispassive():
            slot.activate()

        yield self.passivate()

class AppointmentSlots(sim.Component):

    def process(self):
        while not waitingListPrioritary and waitingListNonPrioritary:
            yield self.passivate()
        self.patientServed = waitingListNonPrioritary.pop()
        yield self.hold(15)
        self.patientServed.activate()

env = sim.Environment(trace=True)

PatientGenerator()
slot = AppointmentSlots()
waitingListPrioritary = sim.Queue("prioritary")
waitingListNonPrioritary = sim.Queue("nonPrioritary")

env.run(till=50)