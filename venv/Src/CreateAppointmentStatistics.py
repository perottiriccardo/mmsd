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

    for vtype in visitTypes:
        docsRate = round(countDocs(mongo, "Appointment_Data", {"Visit type": vtype}), 3)
        print("% " + vtype + ": " + str(docsRate))
    print("-----------------------\n-----------------------")

    for rem in appointmentReminders:
        docsRate = round(countDocs(mongo, "Appointment_Data", {"Appointment remainder": rem}), 3)
        print("% " + rem + ": " + str(docsRate))
    print("-----------------------\n-----------------------")

    for origin in appointmentOrigins:
        docsRate = round(countDocs(mongo, "Appointment_Data", {"Origin of appointment": origin}), 3)
        print("% " + origin + ": " + str(docsRate))
    print("-----------------------\n-----------------------")

    for character in visitCharacters:
        docsRate = round(countDocs(mongo, "Appointment_Data", {"Character of visit": character}), 3)
        print("% " + character + ": " + str(docsRate))
    print("-----------------------\n-----------------------")

    for vstat in visitStatus:
        sum = 0
        for vtype in visitTypes:
            docsRate = round(countDocs(mongo, "Appointment_Data", {"Visit type": vtype, "Visit status": vstat}), 3)
            print(vstat + " at " + vtype + ": " +
                  str(docsRate) + "%")
            sum += docsRate
        print("----------------------- Tot: " + str(round(sum,3)) + " %-----------------------")
    print("-----------------------\n-----------------------")

    for vstat in visitStatus:
        sum = 0
        for rem in appointmentReminders:
            docsRate = round(countDocs(mongo, "Appointment_Data", {"Appointment remainder": rem, "Visit status": vstat}),3)
            print(vstat + " with appointment remainder " + rem + ": " +
                  str(docsRate) + "%")
            sum += docsRate
        print("----------------------- Tot: " + str(round(sum,3)) + " %-----------------------")
    print("-----------------------\n-----------------------")

    for vstat in visitStatus:
        sum = 0
        for origin in appointmentOrigins:
            docsRate = round(countDocs(mongo, "Appointment_Data", {"Origin of appointment": origin, "Visit status": vstat}),3)
            print(vstat + " with origin " + origin + ": " +
                  str(docsRate) + "%")
            sum += docsRate
        print("----------------------- Tot: " + str(round(sum,3)) + " %-----------------------")

    print("-----------------------\n-----------------------")

    for vstat in visitStatus:
        sum = 0
        for character in visitCharacters:
            docsRate = round(countDocs(mongo, "Appointment_Data", {"Character of visit": character, "Visit status": vstat}),3)
            print(vstat + " with visit character " + character + ": " +
                  str(docsRate) + "%")
            sum += docsRate
        print("----------------------- Tot: " + str(round(sum,3)) + " %-----------------------")