# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
import statistics
import math

def countDocs(mongoInstance, collectionName, parameters):
    totalAppointments = mongoInstance.db[collectionName].count_documents({})
    docs = mongoInstance.db[collectionName].count_documents(parameters)
    return (docs / totalAppointments) * 100

def appointmentPerDay(mongoInstance):
    return mongoInstance.db["Appointment_Data"].aggregate([
        {"$match":
             {"$or": [{"Visit status": "Done"}, {"Visit status": "NoShowUp"}]}
         },
        {"$group": {"_id": {"$substr": ["$Visit day", 0, 10]}, "total": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ])

def appointmentPerWeekDay(mongoInstance, day):
    return mongoInstance.db["Appointment_Data"].aggregate([
        {"$match":
             {
                "$and" : [
                    {"$or": [{"Visit status": "Done"}, {"Visit status": "NoShowUp"}]},
                    { "Week day" : day }
                ]
             }

         },
        {"$group": {"_id": {"$substr": ["$Visit day", 0, 10]}, "total": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ])

def doctorsPerSlotMean(mongoInstance, slotM, startH, endH):
   return statistics.mean([g["total"] / (((endH-startH)*60)/slotM) for g in appointmentPerDay(mongoInstance)])

with MongoDB() as mongo:
    visitTypes = ["First", "Revision", "Non-presential", "Special"]
    visitStatus = ["NoShowUp", "Cancelled HS", "Cancelled Pat", "Done", "Other"]
    visitCharacters = ["Ordinary", "Preferential","Non-presential", "Results", "Extra"]
    appointmentOrigins = ["Family doctor", "Specialist doctor", "Other"]
    appointmentReminders = ["Phone", "SMS", "Phone+SMS", "Other", "None"]

    #Conta il numero di appuntamenti contemporanei per determinare il numero di dottori
    for i in range(1,40):
        groups = mongo.db["PatientTrace"].aggregate([
            {"$unwind": "$appointments"},
            {"$match":
                {
                    "$and": [
                        {"$or": [{"appointments.Visit status": "Done"}, {"appointments.Visit status": "NoShowUp"}]},
                        {"appointments.Visit day": {"$not": {"$regex": ".*T00:00:00.*"}}}
                    ]
                }
            },
            {"$group": {"_id": "$appointments.Visit day", "total": {"$sum": 1}}},
            {"$sort": {"total": 1}}
        ])

        print(f"{i} - {sum(el['total'] == i for el in groups)}")

    # print(f"Appointment per day mean: {statistics.mean([g['total'] for g in appointmentPerDay(mongo)])}")
    # #Considerando slot di diversi minutaggi
    # slots = [5,10,15,20,25,30]
    # for slot in slots:
    #     print(f"{slot} minutes slot - {math.ceil(doctorsPerSlotMean(mongo, slot, 8, 21))} doctors")
    #
    # #Data fissata per riscontro slot durata
    # # for a in mongo.query("Appointment_Data", query={ "Visit day" : {"$regex" : "2017-03-21.*"}}, projection={"Visit day": 1}).sort("Visit day", 1):
    # #     print(a["Visit day"][11:])
    #
    # days = ["Mond", "Tuesd", "Wedn", "Thursd", "Friday"]
    # for day in days:
    #     print(
    #         f"Mean doctors value for each week day"
    #         f"{statistics.mean([g['total'] / (((21 - 8) * 60) / 15) for g in appointmentPerWeekDay(mongo, day)])}")
    #
    # for vtype in visitTypes:
    #     docsRate = round(countDocs(mongo, "Appointment_Data", {"Visit type": vtype}), 3)
    #     print("% " + vtype + ": " + str(docsRate))
    # print("-----------------------\n-----------------------")
    #
    # for rem in appointmentReminders:
    #     docsRate = round(countDocs(mongo, "Appointment_Data", {"Appointment remainder": rem}), 3)
    #     print("% " + rem + ": " + str(docsRate))
    # print("-----------------------\n-----------------------")
    #
    # for origin in appointmentOrigins:
    #     docsRate = round(countDocs(mongo, "Appointment_Data", {"Origin of appointment": origin}), 3)
    #     print("% " + origin + ": " + str(docsRate))
    # print("-----------------------\n-----------------------")
    #
    # for character in visitCharacters:
    #     docsRate = round(countDocs(mongo, "Appointment_Data", {"Character of visit": character}), 3)
    #     print("% " + character + ": " + str(docsRate))
    # print("-----------------------\n-----------------------")
    #
    # for vstat in visitStatus:
    #     sum = 0
    #     for vtype in visitTypes:
    #         docsRate = round(countDocs(mongo, "Appointment_Data", {"Visit type": vtype, "Visit status": vstat}), 3)
    #         print(vstat + " at " + vtype + ": " +
    #               str(docsRate) + "%")
    #         sum += docsRate
    #     print("----------------------- Tot: " + str(round(sum,3)) + " %-----------------------")
    # print("-----------------------\n-----------------------")
    #
    # for vstat in visitStatus:
    #     sum = 0
    #     for rem in appointmentReminders:
    #         docsRate = round(countDocs(mongo, "Appointment_Data", {"Appointment remainder": rem, "Visit status": vstat}),3)
    #         print(vstat + " with appointment remainder " + rem + ": " +
    #               str(docsRate) + "%")
    #         sum += docsRate
    #     print("----------------------- Tot: " + str(round(sum,3)) + " %-----------------------")
    # print("-----------------------\n-----------------------")
    #
    # for vstat in visitStatus:
    #     sum = 0
    #     for origin in appointmentOrigins:
    #         docsRate = round(countDocs(mongo, "Appointment_Data", {"Origin of appointment": origin, "Visit status": vstat}),3)
    #         print(vstat + " with origin " + origin + ": " +
    #               str(docsRate) + "%")
    #         sum += docsRate
    #     print("----------------------- Tot: " + str(round(sum,3)) + " %-----------------------")
    #
    # print("-----------------------\n-----------------------")
    #
    # for vstat in visitStatus:
    #     sum = 0
    #     for character in visitCharacters:
    #         docsRate = round(countDocs(mongo, "Appointment_Data", {"Character of visit": character, "Visit status": vstat}),3)
    #         print(vstat + " with visit character " + character + ": " +
    #               str(docsRate) + "%")
    #         sum += docsRate
    #     print("----------------------- Tot: " + str(round(sum,3)) + " %-----------------------")