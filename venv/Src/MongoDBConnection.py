import pymongo

class MongoDB(object):
    def __init__(self):
        self.client = pymongo.MongoClient("mongodb://localhost:27020/")
        self.db = self.client["MMSD"]

    def __enter__(self):
        return self

    def insert(self, tableName, dict, many = False):
        table = self.db[tableName]

        if not many:
            table.insert_one(dict)
        else:
            table.insert_many(dict)

    def update(self, tableName, query, newValue, many = False):
        table = self.db[tableName]

        if not many:
            table.update_one(query, newValue)
        else:
            table.update_many(query, newValue)

    def delete(self, tableName, query, many = False):
        table = self.db[tableName]

        if not many:
            table.delete_one(query)
        else:
            table.delete_many(query)

    def query(self, tableName, query, one = False):
        table = self.db[tableName]
        return table.find_one(query) if one else table.find(query)

    def __exit__(self, exc_type, exc_value, tracebac):
        self.client.close()