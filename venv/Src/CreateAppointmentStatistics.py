# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB


def countDocs(mongoInstance, collectionName, parameters):
    totalAppointments = mongoInstance.db[collectionName].count_documents({})
    docs = mongoInstance.db[collectionName].count_documents(parameters)
    return (docs / totalAppointments) * 100


with MongoDB() as mongo:
    visitTypes = ["First", "Revision", "Non-presential", "Special"]
    visitStatus = ["NoShowUp", "Cancelled HS", "Cancelled Pat", "Done", "Other"]

    for vstat in visitStatus:
        for vtype in visitTypes:
            print(vstat + " at " + vtype + ": " +
                  str(countDocs(mongo, "Appointment_Data", {"Visit type": vtype, "Visit status": vstat})) + "%")
