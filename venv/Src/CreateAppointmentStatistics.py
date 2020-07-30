# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB

import statistics
import math
from datetime import datetime


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

def appointmentPerDayPerYear(mongoInstance,year):
    return mongoInstance.db["Appointment_Data"].aggregate([
        {"$match":
             {"$and" : [
                 {"$or": [{"Visit status": "Done"}, {"Visit status": "NoShowUp"}]},
                 {"Visit day" : { "$regex" : f"{year}.*"}}
             ]
              }

         },
        {"$group": {"_id": {"$substr": ["$Visit day", 0, 10]}, "total": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ])

def appointmentPerDayMorning(mongoInstance):
    return mongoInstance.db["Appointment_Data"].aggregate([
        {"$match":
            { "$and": [
                {"$or": [{"Visit status": "Done"}, {"Visit status": "NoShowUp"}]},
                {"$or": [{"Visit day": {"$regex": ".*T08:"}},
                         {"Visit day": {"$regex": ".*T09:"}},
                         {"Visit day": {"$regex": ".*T10:"}},
                         {"Visit day": {"$regex": ".*T11:"}},
                         {"Visit day": {"$regex": ".*T12:"}},
                         {"Visit day": {"$regex": ".*T13:"}}
                         ]}
             ]
            }
         },
        {"$group": {"_id": {"$substr": ["$Visit day", 0, 10]}, "total": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ])

def appointmentPerDayAfternoon(mongoInstance):
    return mongoInstance.db["Appointment_Data"].aggregate([
        {"$match":
            { "$and": [
                {"$or": [{"Visit status": "Done"}, {"Visit status": "NoShowUp"}]},
                {"$or": [{"Visit day": {"$regex": ".*T14:"}},
                         {"Visit day": {"$regex": ".*T15:"}},
                         {"Visit day": {"$regex": ".*T16:"}},
                         {"Visit day": {"$regex": ".*T17:"}},
                         {"Visit day": {"$regex": ".*T18:"}},
                         {"Visit day": {"$regex": ".*T19:"}},
                         {"Visit day": {"$regex": ".*T20:"}},
                         {"Visit day": {"$regex": ".*T21:"}},
                         {"Visit day": {"$regex": ".*T00:00:00"}}
                         ]}
             ]
            }
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

def doctorsPerSlotMeanMorning(mongoInstance, slotM, startH, endH):
   return statistics.mean([g["total"] / (((endH-startH)*60)/slotM) for g in appointmentPerDayMorning(mongoInstance)])

def doctorsPerSlotMeanAfternoon(mongoInstance, slotM, startH, endH):
   return statistics.mean([g["total"] / (((endH-startH)*60)/slotM) for g in appointmentPerDayAfternoon(mongoInstance)])

def appointmentContemporanei(mongoInstance, start, end):
    tot = 0
    for i in range(1, 19):
        groups = mongoInstance.db["PatientTrace"].aggregate([
            {"$unwind": "$appointments"},
            {"$match":
                 {"$or": [{"appointments.Visit status": "Done"}, {"appointments.Visit status": "NoShowUp"}]}
             },
            {"$group": {"_id": "$appointments.Visit day", "total": {"$sum": 1}}},
            {"$sort": {"total": 1}}
        ])

        s = sum([1 for el in groups if el['total'] == i and (start <= datetime.fromtimestamp(el['_id'] / 1000).hour < end)])
        tot += (s * i)
        print(f"{i} - {s}")
    print(tot)

def totalAppointmentBeforeAndAfter14():
    sumBefore14 = 0
    sumAfter14 = 0
    for i in range(8, 22):
        if i < 14:
            sumBefore14 += mongo.db["Appointment_Data"].count_documents(
                {
                    "$and":[
                        {"Visit day" : { "$regex" : f".*T{i:02d}:.*"}},
                            {"$or":
                                 [
                                {"Visit status": "Done"},
                                {"Visit status": "NoShowUp"}
                                ]
                            }
                        ]
                }
            )
        else:
            sumAfter14 += mongo.db["Appointment_Data"].count_documents(
                {
                    "$and": [
                        {"Visit day": {"$regex": f".*T{i:02d}:.*"}},
                        {"$or":
                            [
                                {"Visit status": "Done"},
                                {"Visit status": "NoShowUp"}
                            ]
                        }
                    ]
                }
            )

    print(sumBefore14, sumAfter14)

def generalStats():
    visitTypes = ["First", "Revision", "Non-presential", "Special"]
    visitStatus = ["NoShowUp", "Cancelled HS", "Cancelled Pat", "Done", "Other"]
    visitCharacters = ["Ordinary", "Preferential", "Non-presential", "Results", "Extra"]
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

with MongoDB() as mongo:
    #appointmentContemporanei(mongo, 14, 22)
    #appointmentContemporanei(mongo, 8, 14)

    # for year in range(2012,2018):
    #     print(year)
    #     print(f"Appointment per day mean: {statistics.mean([g['total'] for g in appointmentPerDayPerYear(mongo,year)])}")
    # print(f"Appointment per day mean: {statistics.mean([g['total'] for g in appointmentPerDay(mongo)])}")
    # #Considerando slot di diversi minutaggi
    # slots = [5,10,15,20,25,30]
    # for slot in slots:
    #     print(f"{slot} minutes slot - {math.ceil(doctorsPerSlotMean(mongo, slot, 8, 21))} doctors")

    slots = [5,10,15,20,25,30]
    for slot in slots:
       print(f"{slot} minutes slot - {math.ceil(doctorsPerSlotMeanMorning(mongo, slot, 8, 14))} doctors")

    for slot in slots:
       print(f"{slot} minutes slot - {math.ceil(doctorsPerSlotMeanAfternoon(mongo, slot, 14, 22))} doctors")

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


