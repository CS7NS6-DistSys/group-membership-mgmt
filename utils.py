#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 16 09:49:41 2018

@author: amit
"""


def insertIfNotPresent(collection, doc):
    
    #if already present then update
    if '_id' in doc :
        doc = collection.update({'_id':doc['_id']}, doc)
    else:
       doc = collection.insert_one(doc) 
       
    return doc