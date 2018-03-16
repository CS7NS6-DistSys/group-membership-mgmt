#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 10 18:58:52 2018

@author: amit
"""
import constants
import socket 
import threading
import json
import model
import traceback

class ServerSocket(threading.Thread):
    
    server_socket = None
    host = None
    collection = None
    
    def __init__(self, port):
        threading.Thread.__init__(self)
        
        print("Instantiating server socket on port "+str(port)+" ...")
        host = '127.0.0.1'
        
        # Create a server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # get local machine name
        self.server_socket.bind((host, port))
        
        # queue up to 5 requests
        self.server_socket.listen(5)
        
        dbConn = model.PyMongoModel()
        self.collection = dbConn.getCollection("process_"+str(port))
    
    def run(self):
         # initiate listening
        self.initiateListening()
        
    def initiateListening(self):
        while True:
            
            clientsocket = None
            try:
                # establish a connection
                clientsocket,addr = self.server_socket.accept()      
            
                print("Got a connection from %s" % str(addr))
                msg = clientsocket.recv(4096)
                recvd_msg = json.loads(msg)
                topic = recvd_msg['topic']
                
                print("Message Topic: "+topic)
               
                # Check if invalid message received
                if topic not in constants.topic:
                    clientsocket.send("Invalid message! This incident will be reported.\n\r"
                                     .encode('ascii'))
                    
                   
                elif topic == 'JOIN_REQUEST':
                    # If not server then return Address of server
                    
                    # else if server then add this to list of known addresses
                    # addresses and return membership view
                    doc = self.collection.find_one()

                    
                    # if view of membership is already created
                    if doc is not None and 'viewOfMembership' in doc:
                        doc['viewOfMembership'].append({'address':addr, 'isMember':True})
                        doc = self.collection.update({'_id':doc['_id']}, doc)
                    else:
                        # create new document
                        doc = {}
                        doc['viewOfMembership'] = [{'address':addr, 'isMember':True}]
                        doc = self.collection.insert_one(doc)
                    
                    # send a key
                    clientsocket.send((json.dumps({"topic":'APPROVED', "key":"This is some key"}))
                    .encode('utf-8'))
                    
                # check type of message received and perform corressponding action
                elif topic == 'GIVE_MEMBERSHIP_VIEW':
                    # query for membership view
                    doc = self.collection.find_one()
                   
                    # send membership view
                    clientsocket.send((json.dumps({'viewOfMembership':doc['viewOfMembership']}))
                    .encode('utf-8'))
                    
                
                       
            except Exception as ex:
                traceback.print_tb(ex.__traceback__)
                print("ERROR: Exception caught on server")
                
            finally:
                clientsocket.close()
                
                    
