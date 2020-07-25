import pymongo
# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
from datetime import datetime


def floor_dt(dt, delta):
    return dt - (dt % delta)

with MongoDB() as mongo:
    trace = []
    i = 0
    for patient in mongo.query("Patients", query = {}, projection = {'Pac_Unif_Cod': 1, 'Age': 1, 'Gender': 1}):
        patient['appointments'] = []
        firstAppointment = True
        for appointment in mongo.query("Appointment_Data", query = {'Pac_Unif_Cod': patient['Pac_Unif_Cod']}, projection = {'_id': 0, 'Month': 0, 'Week day': 0, 'Hour': 0, 'Pac_Unif_Cod': 0, 'Days in waiting list': 0})\
                .sort([('Waiting list entry date', pymongo.ASCENDING), ('Visit day', pymongo.ASCENDING)]):
            try:
                min = datetime.fromtimestamp(1325372400)
                max = datetime.fromtimestamp(datetime.strptime(appointment['Visit day'], "%Y-%m-%dT%H:%M:%S.%f").timestamp())

                appointment['Visit day'] = floor_dt(datetime.strptime(appointment['Visit day'], "%Y-%m-%dT%H:%M:%S.%f").timestamp() * 1000, 300000)
                appointment['relative_visit_day'] = (max-min).days + int((max.hour*60 + max.minute)/5*3.47)/1000 # 5 = minuti, 3.47 = 5 minuti nella simulazione

                max = datetime.fromtimestamp(datetime.strptime(appointment['Waiting list entry date'], "%Y-%m-%dT%H:%M:%S.%f").timestamp())

                appointment['Waiting list entry date'] = datetime.strptime(appointment['Waiting list entry date'], "%Y-%m-%dT%H:%M:%S.%f").timestamp() * 1000
                appointment['relative_waiting_list_entry_date'] = (max-min).days

                if appointment['relative_waiting_list_entry_date'] < 0 or appointment['Visit day'] < appointment['Waiting list entry date']:
                    continue
                if firstAppointment:
                    patient['relative_first_interaction_day'] = (max-min).days
                    firstAppointment = False
            except:
                continue
            patient['appointments'].append(appointment)

        patient['morbility'] = []
        for morbility in mongo.query("Morbility", query = {'pac_unif_cod': patient['Pac_Unif_Cod']}, projection = {'_id': 0, 'Diag_Name': 0, 'pac_unif_cod': 0}):
            try:
                morbility['Initial date'] = datetime.strptime(morbility['Initial date'], "%Y-%m-%dT%H:%M:%S.%f").timestamp() * 1000
            except:
                continue
            try:
                morbility['End date'] = datetime.strptime(morbility['End date'], "%Y-%m-%dT%H:%M:%S.%f").timestamp() * 1000
            except:
                morbility['End date'] = None

            patient['morbility'].append(morbility)

        trace.append(patient)

        i += 1
        if i % 500 == 0:
            mongo.insert('PatientTrace', trace, many = True)
            trace = []

    mongo.insert('PatientTrace', trace, many=True)
