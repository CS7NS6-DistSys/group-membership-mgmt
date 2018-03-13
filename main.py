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


import os
import argparse
import time


import server_socket
import client_socket

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
    exit()

# Host a server
server = server_socket.ServerSocket(args.port)
server.start()

# ping other nodes for membership view
# If it is not coordinator
if not args.isCoordinator:
    client = client_socket.ClientSocket()
    client.sendMessage(port = args.coordinatorPort ,message = "Hello");

# update the membership view

# send the updated membership view
    
print("Terminating process running on "+str(args.port)+" ...")

