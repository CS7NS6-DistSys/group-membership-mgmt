#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 18:26:57 2018

@author: amit

For now we will consider that one server with particular ip:port is the 
coordinator

On coordinator failure, process with highest port no will become the coordinator

The process id of each process is the port number itself.
"""

import argparse
import json
import traceback
import sys
import time

import server_socket
import client_socket
import model
import utils

parser = argparse.ArgumentParser(description='Group Membership Management')

# Command Line Args
parser.add_argument('--isCoordinator', type=bool, default=False, help='True if this is the coordinator')
parser.add_argument('--coordinatorPort', type=int, default=10000, help='Port on which coordinator is running')
parser.add_argument('--port', type=int, help='Run this process on port')
parser.add_argument('--groupName', type=str, help='Name of the group when creating new coordinator or joining the group')

args = parser.parse_args()

# If coordinator then port and coordinator port is same
if args.isCoordinator:
    print("This process is the coordinator process! Say 'Hi' to your master.")
    args.port = args.coordinatorPort
else:
    print("I am slave with id " + str(args.port) + "...")

if not args.port:
    print("Please provide a port number for this process. Arg --port")
    sys.exit()
if not args.groupName:
    print("Please provide a group name to join or create. Arg --groupName")
    sys.exit()

coordinatorPort = args.coordinatorPort

# --------- checking if a port is already running or dead -----------------
client = client_socket.ClientSocket()
running = client.chkStatus(args.port)

# ----------- if not args.port is not running, start the server ------------
if not running:
    # Host a server
    server = server_socket.ServerSocket(args.port, args.groupName)
    server.start()


# Initiate database connection
dbConn = model.PyMongoModel()
# this list maintain common group information
groupList = dbConn.getCollection(str(args.groupName))
# IF A MEMBER NODE i.e. NOT COORDINATOR
if not args.isCoordinator:

    if groupList.find_one() is not None:
        collectionSlave = None
        collectionCoord = None

        try:
            collectionCoord = dbConn.getCollection("process_" + str(coordinatorPort))
            collectionSlave = dbConn.getCollection("process_" + str(args.port))
            docCoord = collectionCoord.find_one()
            doc = collectionSlave.find_one()
            gDoc = groupList.find_one()
            for member in gDoc['viewOfMembership']:
                isCoord = member['isCoordinator']
                if isCoord:
                    coordPort = member['address']
                    coordinatorPort = member['address']
                    # initiate join request
                    join_req_msg = json.dumps({'topic': 'JOIN_REQUEST', 'address': args.port,
                                               'isCoordinator': args.isCoordinator, 'groupName': args.groupName})
                    client = client_socket.ClientSocket()
                    client.sendMessage(port=coordPort, message=join_req_msg.encode('utf-8'));
                    #        print("Request to master sent: {}".format(join_req_msg))

                    join_req_resp = json.loads(client.recvMessage(4096))
                    #        print("Response from master: {}".format(join_req_resp))

                    # If join request approved
                    if join_req_resp['topic'] == "APPROVED":

                        print("\n\nJoin Approved!\n\n")
                    else:
                        print("\n\nGroup join request declined by master. Suiciding. Bye!\n\n")
                        sys.exit()

        except Exception as ex:
            traceback.print_tb(ex.__traceback__)
            print("ERROR: Exception thrown when connecting to master.")
            print("Unable to join group. Suiciding. Bye!")
            sys.exit()

        finally:
            client.close()
        # Request for initial MEMBERSHIP_VIEW
        mem_view_msg = json.dumps({'topic':'GIVE_MEMBERSHIP_VIEW'})
        client = client_socket.ClientSocket()
        client.sendMessage(port=coordinatorPort, message=mem_view_msg.encode('utf-8'));
        view_of_membership = client.recvMessage(4096)
        view_of_membership = json.loads(view_of_membership)
        collection = dbConn.getCollection("process_" + str(args.port))
        # insert the view of membership in the database
        doc = collection.find_one()
        if not running:
            doc = {}
            doc['viewOfMembership'] = view_of_membership['viewOfMembership']
            utils.insertIfNotPresent(collection, doc)
        else:
            for i in view_of_membership['viewOfMembership']:
                doc['viewOfMembership'].append(i)
                collection.update({'_id': doc['_id']}, doc)
                doc = collection.find_one()
        # client.close()

        time.sleep(5)
    else:
        print("No group exist with the given name, Unable to join group")
        sys.exit()


else:
    collection = dbConn.getCollection("process_" + str(coordinatorPort))
    groupList = dbConn.getCollection(str(args.groupName))
    doc = collection.find_one()
    groupDoc = groupList.find_one()
    if doc is None:
        doc = {}
        doc['viewOfMembership'] = [
            {'groupName': args.groupName,'address': coordinatorPort, 'isMember': True, 'key': 'SAMPLE_KEY',
             'isCoordinator': args.isCoordinator}
        ]
        doc = collection.insert_one(doc)
    else:
        collection.delete_one({'_id': doc['_id']})
        doc['viewOfMembership'].append(
            {'groupName': args.groupName, 'address': coordinatorPort, 'isMember': True, 'key': 'SAMPLE_KEY',
             'isCoordinator': args.isCoordinator})
        doc = collection.update({'_id': doc['_id']}, doc)
    if groupDoc is None:
        groupDoc = {}
        groupDoc['viewOfMembership'] = [
            {'groupName': args.groupName, 'address': coordinatorPort, 'isMember': True, 'key': 'SAMPLE_KEY',
             'isCoordinator': args.isCoordinator}]
        groupDoc = groupList.insert_one(groupDoc)
    else:
        groupList.delete_one({'_id': groupDoc['_id']})
        groupDoc['viewOfMembership'].append(
            {'groupName': args.groupName, 'address': coordinatorPort, 'isMember': True, 'key': 'SAMPLE_KEY',
             'isCoordinator': args.isCoordinator})
        groupDoc = groupList.update({'_id': groupDoc['_id']}, groupDoc)



while True:
    j = 0
    collection = dbConn.getCollection("process_" + str(args.port))
    doc = collection.find_one()
    gDoc = groupList.find_one()

    # Iterate over each member in the list and send a PING request to check
    # their alive status.
    # Update membership view accordingly
    print("\n\nPinging all nodes to update membership view...")
    i = 1
    for member in doc['viewOfMembership']:
        member_port = member['address']
        failDetector = {}

        if member_port != args.port:
            client = client_socket.ClientSocket()
            alive_status_msg = {'topic': 'PING', 'msg':args.port}

            isSuccessSend = client.sendMessage(port=member_port,
                                                   message=json.dumps(alive_status_msg).encode('utf-8'))
            if not isSuccessSend:
                print("\n \n----message sending failed to----: ", member_port, "\n \n")
                print("\n \n---------Detecting if failed is Coordinator?------------: ", member_port, "\n \n")
                # failDetector[member_port] = i
                # --------------------- detection for coordinator failure --------------------------
                if member['isCoordinator']:
                    print("\n \n ------ Coordinator failed ------ highest node will be new Coordinator now------ \n \n")
                    # ---------------- removing dead coordinator from the list of member ---------------------
                    collection.update({}, {'$pull': {'viewOfMembership': {'groupName': member['groupName'],
                                                                          'address': member_port}}}, True)
                    doc = collection.find_one()
                    highestPort = 0
                    for newCoord in doc['viewOfMembership']:
                        if newCoord['groupName'] == member['groupName'] and highestPort < newCoord['address']:
                            highestPort = newCoord['address']

                    # ------------------------ assigning highest port as coordinator --------------------------#

                    collection.find_and_modify(query={'viewOfMembership.groupName': member['groupName'],
                                                      'viewOfMembership.address': highestPort},
                                               update={'$set': {'viewOfMembership.$.isCoordinator': True}})

                    # ------------------ updating the group list for new coordinator -----------------------
                    groupList = dbConn.getCollection(member['groupName'])
                    gDoc = groupList.find_one()
                    if gDoc is not None:
                        groupList.update({}, {'$pull': {'viewOfMembership': {'groupName': member['groupName'],
                                                                             'address': member_port}}}, True)
                        gDoc = groupList.find_one()
                        for mem in gDoc['viewOfMembership']:
                            if mem['address'] == highestPort:
                                if not mem['isCoordinator']:
                                    groupList.find_and_modify(query={'viewOfMembership.groupName': member['groupName'],
                                                                     'viewOfMembership.address': highestPort},
                                                              update={
                                                                   '$set': {'viewOfMembership.$.isCoordinator': True}})
                else:
                    # ----------------case for member failure --------------------
                    print("\n \n----failed node not a coordinator----: ", member_port, "\n \n")
                    print('removing the dead node from the group ', member_port)
                    # ---------------updating self list for node failure ----------------
                    collection.update({}, {'$pull': {'viewOfMembership': {'groupName': member['groupName'],
                                                                          'address': member_port}}}, True)
                    # ---------------updating group list for node failure ----------------
                    groupList = dbConn.getCollection(member['groupName'])
                    gDoc = groupList.find_one()
                    if gDoc is not None:
                        groupList.update({}, {'$pull': {'viewOfMembership': {'groupName': member['groupName'],
                                                                             'address': member_port}}}, True)
            else:
                i = 1
                mem_resp = client.recvMessage(4096)

            print(member)
            client.close()

    # collection.update({'_id': doc['_id']}, doc)
    # groupList.update({'_id': gDoc['_id']}, gDoc)
    time.sleep(5)


# update the membership view

# send the updated membership view

# print("Terminating process running on {}...".format(str(args.port)))

