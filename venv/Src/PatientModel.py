import salabim as sim
import numpy as np
import configparser

class PatientGenerator(sim.Component):
    def process(self):
        while True:
            Patient()
            print(env.now())
            yield self.hold(sim.Uniform(5, 15, 'hours').sample())

class Patient(sim.Component):
    def process(self):
        self.enter(waitingListNonPrioritary) if np.random.choice(2, 1,
                                                                 p=[1 - float(config['Probabilities']['patientPrioritary']),
                                                                    config['Probabilities']['patientPrioritary']
                                                                    ]) == 0 else self.enter(waitingListPrioritary)
        # TODO Inserire un timeout se appointmentslot è passivo e arriva un paziente in coda
        if slot.ispassive():
            slot.activate()

        yield self.passivate()

class AppointmentSlots(sim.Component):
    def process(self):
        while not waitingListPrioritary and not waitingListNonPrioritary:
            yield self.passivate()

        if not waitingListPrioritary:
            self.patientServed = waitingListNonPrioritary.pop()
        elif not waitingListNonPrioritary:
            self.patientServed = waitingListPrioritary.pop()
        else:
            self.patientServed = waitingListNonPrioritary.pop() if np.random.choice(2, 1,
                                                                                    p=[1 - float(config['Probabilities']['servePrioritary']),
                                                                                       config['Probabilities']['servePrioritary']
                                                                                       ]) == 0 else waitingListPrioritary.pop()

        yield self.hold(env.minutes(30))
        self.patientServed.activate()

    # def availableSlots(self):
    #     actualDay = int(env.now())
    #     if actualDay > self.day:
    #         self.remainingSlots =
    #         self.day = actualDay
    #         self.remainingSlots -= 1


config = configparser.ConfigParser()
config.read('ConfigFile.properties')

env = sim.Environment(trace=True, time_unit='days')

PatientGenerator()
slot = AppointmentSlots()
waitingListPrioritary = sim.Queue("prioritary")
waitingListNonPrioritary = sim.Queue("nonPrioritary")

env.run(till=50)