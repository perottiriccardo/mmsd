# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
from datetime import datetime

with MongoDB() as mongo:
    trace = []
    i = 0
    for patient in mongo.query("Patients", query = {}, projection = {'Pac_Unif_Cod': 1, 'Age': 1, 'Gender': 1}):
        patient['appointments'] = []
        firstAppointment = True
        for appointment in mongo.query("Appointment_Data", query = {'Pac_Unif_Cod': patient['Pac_Unif_Cod']}, projection = {'_id': 0, 'Month': 0, 'Week day': 0, 'Hour': 0, 'Pac_Unif_Cod': 0, 'Days in waiting list': 0}):
            try:
                min = datetime.fromtimestamp(1325372400)
                max = datetime.fromtimestamp(datetime.strptime(appointment['Visit day'], "%Y-%m-%dT%H:%M:%S.%f").timestamp())

                appointment['Visit day'] = datetime.strptime(appointment['Visit day'], "%Y-%m-%dT%H:%M:%S.%f").timestamp() * 1000
                appointment['relative_visit_day'] = (max-min).days

                max = datetime.fromtimestamp(datetime.strptime(appointment['Waiting list entry date'], "%Y-%m-%dT%H:%M:%S.%f").timestamp())

                appointment['Waiting list entry date'] = datetime.strptime(appointment['Waiting list entry date'], "%Y-%m-%dT%H:%M:%S.%f").timestamp() * 1000
                appointment['relative_waiting_list_entry_date'] = (max-min).days

                #TODO togliere anche appuntamenti con visit day precedente a waiting list entry date
                if appointment['relative_waiting_list_entry_date'] < 0:
                    continue
                if firstAppointment:
                    patient['relative_first_interaction_day'] = (max-min).days
                    firstAppointment = False
            except:
                continue
            patient['appointments'].append(appointment)

        patient['appointments'] = sorted(patient['appointments'], key=lambda k: k['Visit day'])

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
