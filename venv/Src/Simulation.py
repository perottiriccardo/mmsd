# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
import salabim as sim
import numpy as np
import configparser
import math
import image

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
            Appointment(nAppointment=i+1, pateintId=self.id, info=self.appointments[i])

            if(i < len(self.appointments)-1):
                # Il paziente attende la data di waiting list del successivo appuntamento per creare il nuovo appuntamento
                yield self.hold(self.appointments[i+1]['relative_waiting_list_entry_date'] - env.now())

class Appointment(sim.Component):
    def setup(self, nAppointment, pateintId, info):
        self.nAppointment = nAppointment
        self.pateintId = pateintId
        self.info = info

    def process(self):
        global nAppointments, noShowUp, done, cancelled

        #print(f"Appointment schedule {self.nAppointment} -> Patient: {self.pateintId}")
        nAppointments += 1

        if self.info['Visit status'] == 'Cancelled Pat' or self.info['Visit status'] == 'Cancelled HS':
            # Attendo un valore tra 0 e i giorni che mancano alla visita per cancellare l'appuntamento
            yield self.hold(sim.Uniform(0, int(self.info['relative_visit_day'] - env.now())))
            #print(f"Appointment cancelled {self.nAppointment} -> Patient: {self.pateintId}")
            cancelled += 1
        else:
            # Attendo fino al giorno dell'appuntamento
            yield self.hold(self.info['relative_visit_day'] - env.now())

            if str(env.now())[-2:] == ".0":
                yield self.hold(sim.Uniform(14, 19, "hours"))

            # Richiedo una risorsa slot
            yield self.request(slots)

            if self.info['Visit status'] == 'NoShowUp':
                #print(f"Appointment no show up {self.nAppointment} -> Patient: {self.pateintId}")

                # Tengo lo slot occupato per 15 minuti
                yield self.hold(env.minutes(timeSlot))
                self.release(slots)
                noShowUp +=1
            else:
                # Richiedo una risorsa dottore
                yield self.request(doctors)
                # Quando il dottore è disponibile faccio la visita di 15 minuti
                yield self.hold(env.minutes(timeSlot))

                # Rilascio la risorsa dottore
                self.release(doctors)
                self.release(slots)
                done +=1

                #print(f"Appointment done {self.nAppointment} -> Patient: {self.pateintId}")

class DepartmentCapacity(sim.Component):
    def process(self):
        exceedRequesters = 0
        while True:
            if int(math.ceil(env.now())) % 7 == 0 or int(math.ceil(env.now())) % 7 == 6:
                slots.set_capacity(0)
                doctors.set_capacity(0)
                yield self.hold(1)
            else:
                slots.set_capacity(0)
                doctors.set_capacity(0)
                yield self.hold(env.hours(8))

                slots.set_capacity(11)
                doctors.set_capacity(11)
                yield self.hold(env.hours(6))

                exceedRequesters += len(slots.requesters())
                print(f"{int(env.now())} -> {len(slots.requesters())} -> total {exceedRequesters}")
                slots.set_capacity(3)
                doctors.set_capacity(3)
                yield self.hold(env.hours(8))

                slots.set_capacity(0)
                doctors.set_capacity(0)
                yield self.hold(env.hours(2))




nAppointments = 0
noShowUp = 0
done = 0
cancelled = 0

# config = configparser.ConfigParser()
# config.read('ConfigFile.properties')

timeSlot = 20
#for ts in (5,10,15,20):
env = sim.Environment(trace=False, time_unit='days')
env.animate(True)
#timeSlot = ts
PatientGenerator()
# Creata la risorsa slot con una capacità di 6
slots = sim.Resource('Slot', capacity=11)
# Creata la risorsa dottore con una capacità di 6
doctors = sim.Resource('Doctor', capacity=11)
DepartmentCapacity()

env.modelname("Patients not show up simulation")
env.background_color("20%gray")
env.speed(0.4)

sim.AnimateQueue(slots.requesters(), x=30, y=650, title='Requester queue', direction='e', id='blue')
sim.AnimateQueue(slots.claimers(), x=30, y=580, title='Claimers queue', direction='e', id='blue')
sim.AnimateMonitor(slots.available_quantity, x=10, y=480, width=950, height=50, horizontal_scale=600, vertical_scale=8)
sim.AnimateMonitor(slots.claimed_quantity, x=10, y=400, width=950, height=50, horizontal_scale=600, vertical_scale=8)
sim.AnimateMonitor(slots.occupancy, x=10, y=320, width=950, height=50, horizontal_scale=600, vertical_scale=8)

sim.AnimateText(text=lambda: slots.print_info(as_str=True), x=10, y=270,
                text_anchor='nw', font='narrow', fontsize=14)

env.run(till=2200)

slots.print_statistics()
doctors.print_statistics()

print(f"Appointments: {nAppointments}")
print(f"NoShowUp: {noShowUp/nAppointments*100}")
print(f"Done: {done/nAppointments*100}")
print(f"Cancelled: {cancelled/nAppointments*100}")

#3.8 clamed quantity desiderata