#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 10 18:58:52 2018

@author: amit
"""
import socket 
import threading

class ServerSocket(threading.Thread):
    
    server_socket = None
    host = None
    
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
        
        # initiate listening
        # self.initiateListening()
    
    def run(self):
        self.initiateListening()
        
    def initiateListening(self):
         while True:
           # establish a connection
           clientsocket,addr = self.server_socket.accept()      
        
           print("Got a connection from %s" % str(addr))
           print(clientsocket.recv(4096))
           msg = 'Hello from the other side!'+ "\r\n"
           clientsocket.send(msg.encode('ascii'))
           clientsocket.close()

