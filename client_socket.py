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
        self.client_socket.connect((ip, port))
        
        self.client_socket.send(message)
        recvd_message = self.client_socket.recv(4096)
        print(recvd_message)
        
        self.client_socket.close()