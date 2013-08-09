# -*- coding: UTF-8 -*-

#Distributed under the MIT licesnse.
#Copyright (c) 2013 Dave McCoy (dave.mccoy@cospandesign.com)

#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import sys
import os
import socket
import time
import re

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from defines import STATUS_PORT
from defines import DATA_PORT

MAX_READ_SIZE = 1024

class PrometheusClientError(Exception):
    pass

class PrometheusClient(object):
    """
    Local Socket server used to facilitate inter process communication
    """
    def __init__(self):
        super (PrometheusClient, self).__init__()



    def send_data(self, data = None, host = 'localhost', port = DATA_PORT):
        """
        Send data to the connected server

        Args:
            data (buffer): Character string
            host (string/IP): Address of the host
                (default = 'localhost' or this computer)
            port (integer): server port on the local host
                (default = default.DATA_PORT probably 0xC595)


        Return:
            Nothing

        Raises:
            PrometheusClientError
                -Data is None
                -Failed to connect to the server
                -Transfer Failure
        """
        if data is None:
            raise PrometheusClientError("Data cannot be set to None")

        client = None
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #For the times where the socket was not closed cleanly
            #client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client.connect((host, port))

        except socket.error, err:
            raise PrometheusClientError("Failed to connecto to server")

        #Check for greeting
        client.settimeout(10)
        #greeting = client.recv(MAX_READ_SIZE)
        #if len(greeting > 0):
        #    print "Received from host: %s" % greeting

        #Attempt to send the data
        try:
            client.sendall(data)
        except socket.error, err:
            raise PrometheusClientError("Failed to send data: %s" % str(err))

        print "Finished Sending Data"
        #I need a way to get feedback from the device

        #Close the socket connection
        client.shutdown(socket.SHUT_RDWR)
        client.close()
        

def vendor_reset_device(host = 'localhost', port = STATUS_PORT, usb_id = "-1:-1"):
    """
    Opens up a connection to the status server and request status and send

    Args:
        host (string/IP): Address of the host
            (default = 'localhost' or this computer)
        port (integer): server port on the local host
            (default = default.STATUS_PORT probably 0xC594)
        usb_id (string): Vendor ID and Product ID in a string format

    Return:
        (String) Status

    Raises:
        Nothing
    """
    client = None
    status = ""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #For the times where the socket was not closed cleanly
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.connect((host, port))

    except socket.error, err:
        if re.search("Errno.*111", str(err)):
            return "No Server Running"

        return "Not Connected to Server: %s" % str(err)

    #Check for greeting
    client.settimeout(1)
    client.sendall("vr%s" % usb_id)

    try:
        status = client.recv(MAX_READ_SIZE)

    except socket.error as err:
        print "Error reading data"

    #Close the socket connection
    client.shutdown(socket.SHUT_RDWR)
    client.close()
    time.sleep(4)
    return status     


 
def get_server_status(host = 'localhost', port = STATUS_PORT):
    """
    Opens up a connection to the status server and request status

    Args:
        host (string/IP): Address of the host
            (default = 'localhost' or this computer)
        port (integer): server port on the local host
            (default = default.STATUS_PORT probably 0xC594)
    Return:
        (String) Status

    Raises:
        Nothing
    """
    client = None
    status = ""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #For the times where the socket was not closed cleanly
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.connect((host, port))

    except socket.error, err:
        if re.search("Errno.*111", str(err)):
            return "No Server Running"

        return "Not Connected to Server: %s" % str(err)

    #Check for greeting
    client.settimeout(1)
    client.sendall("?")
    try:
        status = client.recv(MAX_READ_SIZE)

    except socket.error as err:
        print "Error reading data"

    #Close the socket connection
    client.shutdown(socket.SHUT_RDWR)
    client.close()
    return status     

def is_server_running():
    """
    Check to see if there is a server already running

    Opens up a socket, waits for a response
    """
    client = None
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', STATUS_PORT))
    except socket.error, err:
        #print "Socket Error: %s" % str(err)
        return False

    try:
        data = client.recv(MAX_READ_SIZE)
        #client.send("Does this work??")
        #print "Data Read from Host: %s" % str(data)
        client.shutdown(socket.SHUT_RDWR)
        client.close()
    except socket.error as err:
        #print "Is Server Running? Socket Error: %s" % str(err)
        return False

    return True
    
def get_data_port(server_status = None):
    """
    if server is None then request
    """
    if server_status is None:
        server_status = get_server_status()
    
    lines = server_status.splitlines()
    for line in lines:
        name = line.partition(":")[0]
        #print "Name: %s" % name
        value = line.partition(":")[2].strip()
        value = value.partition("0x")[2]
        if "Data Port" in name:
            #print "Found Data Port"
            return int(value, 16)

    raise PrometheusClientError("Data Port not found int %s" % server_status)

def is_data_server_ready(server_status = None):
    if server_status is None:
        server_status = get_server_status()

    lines = server_status.splitlines()
    for line in lines:
        name = line.partition(":")[0]
        #print "Name: %s" % name
        value = line.partition(":")[2].strip()
        if "Data Server" in name:
            if value == "Connected":
                return False
            return True

    raise PrometheusClientError("Data Port not found int %s" % server_status)

def is_usb_device_attached(server_status = None):
    if server_status is None:
        server_status = get_server_status()

    lines = server_status.splitlines()
    for line in lines:
        name = line.partition(":")[0]
        #print "Name: %s" % name
        value = line.partition(":")[2].strip().lower()
        if "USB Status" in name:
            print "USB value: %s" % value
            if re.search("device.*connect", value):
                return True
            return False

    raise PrometheusClientError("Data Port not found int %s" % server_status)



