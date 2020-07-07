from xml.dom import minidom

patientsFile = minidom.parse('../Resources/4.2.2. Navarra Files/Patients.XML')

patients = patientsFile.getElementsByTagName('Row')
for patient in patients:
    details = patient.getElementsByTagName('Cell')
    for detail in details:
        data = detail.getElementsByTagName('Data')[0].firstChild.data
        print(data)