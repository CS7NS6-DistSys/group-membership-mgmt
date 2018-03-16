#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 18:26:01 2018

@author: amit
"""

import socket

class ClientSocket:

    client_socket = None
    host = None
    
    def __init__(self):
        #create an INET, STREAMing socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    
    def sendMessage(self, port, message, ip = "127.0.0.1"):
        try:        
            self.client_socket.connect((ip, port))
            self.client_socket.send(message)
            print("REQUEST: {}".format(message))
            return True
            
        except socket.error:
            print("ERROR: Exception thrown while sending message to "+ip+":"+str(port))
            return False
            
    
    def recvMessage(self, bytesize):
        recvd_message = self.client_socket.recv(bytesize)
        print("RESPONSE: {} \n\n".format(recvd_message))
        return recvd_message
        
        
    def close(self):
        self.client_socket.close()