from xml.dom import minidom
# noinspection PyUnresolvedReferences
import MongoDBConnection

patientsFile = minidom.parse('../Resources/4.2.2. Navarra Files/Patients.XML')
legend = []

patients = patientsFile.getElementsByTagName('Row')

with MongoDBConnection.MongoDB() as mongo:
    for patient in patients:
        details = patient.getElementsByTagName('Cell')

        if not legend:
            for detail in details:
                legend.append(detail.getElementsByTagName('Data')[0].firstChild.data)
        else:
            row = {}
            for detail, col in zip(details, legend):
                data = detail.getElementsByTagName('Data')[0].firstChild.data
                row[col] = data
            mongo.insert("patients", row)