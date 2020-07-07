from xml.dom import minidom
# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
import glob, os

with MongoDB() as mongo:
    for filePath in glob.glob("../Resources/4.2.2. Navarra Files/*.XML"):
        filename = os.path.splitext(os.path.basename(filePath))[0].replace(" ", "_")

        xmlFile = minidom.parse(filePath)
        rows = xmlFile.getElementsByTagName('Row')

        legend = []
        documents = []
        i = 0
        for row in rows:
            details = row.getElementsByTagName('Cell')

            if not legend:
                legend = [detail.getElementsByTagName('Data')[0].firstChild.data for detail in details]
            else:
                documents.append({col: detail.getElementsByTagName('Data')[0].firstChild.data for detail, col in zip(details, legend)})

                i += 1
                if(i % 10000 == 0):
                    mongo.insert(filename, documents, many=True)
                    documents = []

        mongo.insert(filename, documents, many=True)