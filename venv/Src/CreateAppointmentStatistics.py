# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB


def countDocs(mongoInstance, collectionName, parameters):
    totalAppointments = mongoInstance.db[collectionName].count_documents({})
    docs = mongoInstance.db[collectionName].count_documents(parameters)
    return (docs / totalAppointments) * 100


with MongoDB() as mongo:
    visitTypes = ["First", "Revision", "Non-presential", "Special"]
    visitStatus = ["NoShowUp", "Cancelled HS", "Cancelled Pat", "Done", "Other"]
    visitCharacters = ["Ordinary", "Preferential","Non-presential", "Results", "Extra"]
    appointmentOrigins = ["Family doctor", "Specialist doctor", "Other"]
    appointmentReminders = ["Phone", "SMS", "Phone+SMS", "Other", "None"]

    for vstat in visitStatus:
        print("-----------------------")
        for vtype in visitTypes:
            print(vstat + " at " + vtype + ": " +
                  str(countDocs(mongo, "Appointment_Data", {"Visit type": vtype, "Visit status": vstat})) + "%")

    print("-----------------------")
    print("-----------------------")

    for vstat in visitStatus:
        print("-----------------------")
        for rem in appointmentReminders:
            print(vstat + " with reminder " + rem + ": " +
                  str(countDocs(mongo, "Appointment_Data", {"Appointment remainder": rem, "Visit status": vstat})) + "%")

    print("-----------------------")
    print("-----------------------")

    for vstat in visitStatus:
        print("-----------------------")
        for origin in appointmentOrigins:
            print(vstat + " with appointment origin " + origin + ": " +
                  str(countDocs(mongo, "Appointment_Data", {"Origin of appointment": origin, "Visit status": vstat})) + "%")

    print("-----------------------")
    print("-----------------------")

    for vstat in visitStatus:
        print("-----------------------")
        for character in visitCharacters:
            print(vstat + " with visit character " + character + ": " +
                  str(countDocs(mongo, "Appointment_Data",
                                {"Character of visit": character, "Visit status": vstat})) + "%")