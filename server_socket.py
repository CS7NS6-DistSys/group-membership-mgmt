#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 10 18:58:52 2018

@author: amit
"""
import client_socket
import constants
import model
import utils

import socket
import threading
import json
import traceback


class ServerSocket(threading.Thread):
    server_socket = None
    host = None
    collection = None

    def __init__(self, port, gn):
        threading.Thread.__init__(self)

        print("Instantiating server socket on port " + str(port) + " ...")
        host = '127.0.0.1'

        # Create a server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # get local machine name
        self.server_socket.bind((host, port))

        # queue up to 5 requests
        self.server_socket.listen(5)

        # assigning a self port
        self.port = port

        dbConn = model.PyMongoModel()
        self.collection = dbConn.getCollection("process_" + str(port))
        self.gn = dbConn.getCollection(str(gn))

    def run(self):
        # initiate listening
        self.initiateListening()

    def initiateListening(self):
        while True:

            clientsocket = None
            try:
                # establish a connection
                clientsocket, addr = self.server_socket.accept()

                print("Got a connection from %s" % str(addr))
                msg = clientsocket.recv(4096)
                recvd_msg = json.loads(msg)
                topic = recvd_msg['topic']

                print("Message Topic: " + topic)

                # Check if invalid message received
                if topic not in constants.topic:
                    clientsocket.send(json.dumps({'topic': "Invalid message! "
                                                           + "This incident will be reported."})
                                      .encode('utf-8'))

                elif topic == 'PING':
                    clientsocket.send(json.dumps({'topic': 'PONG', 'msg': self.port}).encode('utf-8'))

                elif topic == 'JOIN_REQUEST':

                    client_addr = recvd_msg['address']
                    isCoordinator = recvd_msg['isCoordinator']
                    groupName = recvd_msg['groupName']

                    # If not server then return Address of server

                    # else if server then add this to list of known addresses
                    # addresses and return membership view
                    key = utils.getKey();
                    doc = self.collection.find_one()
                    # find  the group list
                    groupDoc = self.gn.find_one()

                    # if view of membership is already created
                    if doc is not None and 'viewOfMembership' in doc:

                        doc['viewOfMembership'].append(
                            {'groupName': groupName, 'address': client_addr, 'isMember': True,
                             'isCoordinator': isCoordinator, 'key': key})
                        self.collection.update({'_id': doc['_id']}, doc)
                    else:
                        # create new document
                        doc = {}
                        doc['viewOfMembership'] = [
                            {'groupName': groupName, 'address': client_addr, 'isMember': True,
                             'isCoordinator': isCoordinator, 'key': key}]
                        doc = self.collection.insert_one(doc)

                    # -------------------writing the new information in the group list---------------------------
                    groupDoc = self.gn.find_one()
                    if groupDoc is not None:
                        groupDoc['viewOfMembership'].append(
                            {'groupName': groupName, 'address': client_addr, 'isMember': True,
                             'isCoordinator': isCoordinator, 'key': key})
                        self.gn.update({'_id': groupDoc['_id']}, groupDoc)
                    else:
                        # create new document
                        groupDoc = {}
                        groupDoc['viewOfMembership'] = [
                            {'groupName': groupName, 'address': client_addr, 'isMember': True,
                             'isCoordinator': isCoordinator, 'key': key}]
                        groupDoc = self.gn.insert_one(groupDoc)

                        # -----------------broadcasting the updated view to all other members----------------------
                    print("\n\nBroadcasting updated membership...")
                    # doc = self.collection.find_one()
                    groupDoc = self.gn.find_one()
                    for member in groupDoc['viewOfMembership']:
                        member_port = member['address']

                        if member_port != self.port and member_port != client_addr:
                            client = client_socket.ClientSocket()
                            updatedview = json.dumps({'topic': 'MEMBERSHIP_UPDATE',
                                                      'message': {'viewOfMembership':
                                                                  {'groupName': groupName,
                                                                   'address': client_addr,
                                                                   'isMember': True,
                                                                   'isCoordinator': isCoordinator,
                                                                   'key': key}}}).encode('utf-8')

                            # print("-----", updatedview)
                            isSuccessSend = client.sendMessage(port=member_port,
                                                               message=updatedview)
                            client.close()
                            print(isSuccessSend)

                        print(member)
                    clientsocket.send((json.dumps({"topic": 'APPROVED', "key": key}))
                                      .encode('utf-8'))

                # check type of message received and perform corresponding action
                elif topic == 'GIVE_MEMBERSHIP_VIEW':
                    # query for membership view
                    # doc = self.collection.find_one()
                    groupDoc = self.gn.find_one()
                    # send membership view
                    clientsocket.send((json.dumps({'viewOfMembership': groupDoc['viewOfMembership']}))
                                      .encode('utf-8'))
                # ------------updated membership view ---------------
                elif topic == 'MEMBERSHIP_UPDATE':
                    # when the recieving port is not coordinator

                    # print("2. Updated recieved:", recvd_msg['message'])
                    # doc1 = {}
                    #
                    # doc1['viewOfMembership'] = recvd_msg['message']['viewOfMembership']
                    # # print("3.", doc1)
                    # # print("====this is port: ", self.port)
                    # self.collection.drop()
                    # dbConn = model.PyMongoModel()
                    # collection = dbConn.getCollection("process_" + str(self.port))
                    #
                    # utils.insertIfNotPresent(collection, doc1)
                    doc = self.collection.find_one()
                    if doc is not None:
                        doc['viewOfMembership'].append(recvd_msg['message']['viewOfMembership'])
                        self.collection.update({'_id': doc['_id']}, doc)


            except Exception as ex:
                traceback.print_tb(ex.__traceback__)
                print("ERROR: Exception caught on server")

            finally:
                clientsocket.close()
