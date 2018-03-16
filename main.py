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
import time
import json
import traceback
import sys

import server_socket
import client_socket
import model
import utils

parser = argparse.ArgumentParser(description='Group Membership Management');

# Command Line Args
parser.add_argument('--isCoordinator', type=bool, default = False, help='True if this is the coordinator')
parser.add_argument('--coordinatorPort', type=int, default = 10000, help='Port on which coordinator is running')
parser.add_argument('--port', type=int, help='Run this process on port')

args = parser.parse_args();

# If coordinator then port and coordinator port is same
if args.isCoordinator:
    print("This process is the coordinator process! Say 'Hi' to your master.")
    args.port = args.coordinatorPort
else :
    print("I am slave with id "+str(args.port)+"...")

if not args.port:
    print("Please provide a port number for this process. Arg --port")
    sys.exit()

# Host a server
server = server_socket.ServerSocket(args.port)
server.start()

# Initiate database connection
dbConn = model.PyMongoModel()

# IF A MEMBER NODE i.e. NOT COORDINATOR
if not args.isCoordinator:

    collection = None

    try:
        # initiate join request
        join_req_msg = json.dumps({'topic':'JOIN_REQUEST'})
        client = client_socket.ClientSocket()
        client.sendMessage(port = args.coordinatorPort , message = join_req_msg.encode('utf-8'));
        print("Request to master sent: {}".format(join_req_msg))
        join_req_resp = json.loads(client.recvMessage(4096))
        print("Response from master: {}".format(join_req_resp))
        
        # If join request approved
        if(join_req_resp['topic'] == "APPROVED"):
            collection = dbConn.getCollection("process_"+str(args.port))
            doc = collection.find_one();
            doc['key'] = join_req_resp['key']
#            collection.insert_one(insertDoc)
            utils.insertIfNotPresent(collection, doc)
        else:
            print("Group join request declined by master. Suiciding. Bye!")
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
    client.sendMessage(port = args.coordinatorPort ,message = mem_view_msg.encode('utf-8'));
    view_of_membership = client.recvMessage(4096)
    
    # insert the view of membership in the database
    doc = collection.find_one()
    doc['viewOfMembership'] = view_of_membership
    utils.insertIfNotPresent(collection, doc)
#    collection.insert_one(doc)
    client.close()
    
    while True:
        client = client_socket.ClientSocket()
        client.sendMessage(port = args.coordinatorPort ,message = mem_view_msg.encode('utf-8'));
        view_of_membership = client.recvMessage(4096)
        client.close()
        time.sleep(5)

# update the membership view

# send the updated membership view
    
print("Terminating process running on {}...".format(str(args.port)))


def insertIfNotPresent(collection, doc):
    
    #if already present then update
    if doc is not None:
        doc = collection.update({'_id':doc['_id']}, doc)
    else:
       doc = collection.insert_one(doc) 
       
    return doc