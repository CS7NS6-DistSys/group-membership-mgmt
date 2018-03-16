# -*- coding: utf-8 -*-

from pymongo import MongoClient

class PyMongoModel:
    
    db = None
    
    def __init__(self):
        client = MongoClient('localhost', 27017)
        
        self.db = client.group_membership_mgmt
        
        
    def getCollection(self, collectionName):
        collection = self.db[collectionName]
        return collection