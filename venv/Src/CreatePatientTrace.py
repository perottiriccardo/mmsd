from DBConnection.MongoDBConnection import MongoDB
from datetime import datetime

with MongoDB() as mongo:
    trace = []
    i = 0
    for patient in mongo.query("Patients", query = {}, projection = {'Pac_Unif_Cod': 1, 'Age': 1, 'Gender': 1}):
        patient['appointment'] = []

        for appointment in mongo.query("Appointment_Data", query = {'Pac_Unif_Cod': patient['Pac_Unif_Cod']}, projection = {'_id': 0, 'Month': 0, 'Week day': 0, 'Hour': 0}):
            appointment['Visit day'] = datetime.strptime(appointment['Visit day'], "%Y-%m-%dT%H:%M:%S.%f").timestamp() * 1000
            appointment['Waiting list entry date'] = datetime.strptime(appointment['Waiting list entry date'], "%Y-%m-%dT%H:%M:%S.%f").timestamp() * 1000

            patient['appointment'].append(appointment)

        trace.append(patient)

        i += 1
        if i % 10000 == 0:
            mongo.insert('PatientTrace', trace, many = True)
            trace = []

    mongo.insert('PatientTrace', trace, many=True)