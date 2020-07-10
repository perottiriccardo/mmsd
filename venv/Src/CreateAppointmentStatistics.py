# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB

with MongoDB() as mongo:
    totalAppointments = mongo.db["Appointment_Data"].count_documents({})
    firstNoShowUp = mongo.db["Appointment_Data"].count_documents({ "Visit type": "First", "Visit status": "NoShowUp"})
    nextNoShowUp = mongo.db["Appointment_Data"].count_documents({"Visit type:": {"$ne" : "First"}, "Visit status": "NoShowUp"})
    print(str((firstNoShowUp / totalAppointments)*100) + "%")
    print(str((nextNoShowUp / totalAppointments)*100) + "%")
    #mongo.insert('PatientStatistic', statisticsList, many=True)
