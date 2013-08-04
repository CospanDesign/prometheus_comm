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
import threading
import Queue
import select


sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from defines import VERSION
from defines import PORT




# Echo server program
#
#HOST = ''                 # Symbolic name meaning all available interfaces
#PORT = 50007              # Arbitrary non-privileged port
#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.bind((HOST, PORT))
#s.listen(1)
#conn, addr = s.accept()
#print 'Connected by', addr
#while 1:
#        data = conn.recv(1024)
#            if not data: break
#                conn.sendall(data)
#                conn.close()
#

MAX_READ_SIZE = 1024


class SocketThread(threading.Thread):
    def __init__(self, sock, listen_port, queue, connection_cb, activity_cb):
        super(SocketThread, self).__init__()
        #print "Starting thread listener on port 0x%X" % listen_port
        self.sock = sock
        self.listen_port = listen_port
        self.connection_cb = connection_cb
        self.activity_cb = activity_cb
        self.queue = queue
        conn = None

    def run(self):
        self.sock.bind(('', self.listen_port))
        while True:
            conn = None
            addr = ""
            try:
                self.sock.listen(1)
                
                conn, addr = self.sock.accept()
                #print "Connected by: %s" % str(addr)
                self.connection_cb(conn)
                
                
                while True:
                    try:
                        input_ready, output_list, except_list = select.select([conn], [], [])
                        
                        for s in input_ready:
                            data = s.recv(MAX_READ_SIZE)
                            if not data:
                                #print "Closed Connection"
                                conn.close()
                                self.activity_cb(None)
                        
                            else:
                                #print "Received Data"
                                self.queue.put(data)
                                self.activity_cb(conn)
                    except select.error, err:
                        #print "Select Error"
                        break

            except socket.error, err:
                #print "Socket Error: %s" % str(err)
                return


class PrometheusServer(object):
    """
    Local Socket server used to facilitate inter process communication
    """
    def __init__(self, server_status_cb = None, server_activity_cb = None):
        super (PrometheusServer, self).__init__()
        self.message = "Prometheus Server Version: %s" % VERSION
        self.server_status_cb = server_status_cb
        self.server_activity_cb = server_activity_cb
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.queue = Queue.Queue()
        self.opened = False

        #SO_REUSADDR is nice because if there is a mistake I'm not stuck waiting
        #For the socket to time out
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socket_thread = SocketThread(self.sock,
                                          PORT,
                                          self.queue,
                                          self.connection_cb,
                                          self.activity_cb)

        self.socket_thread.start()


    def send_greeting(self, connection):
        #Send greeting
        connection.sendall(self.message)

    def connection_cb(self, connection):
        self.send_greeting(connection)
        self.opened = True
        if self.server_status_cb is not None:
            self.server_status_cb(True)

    def activity_cb(self, connection):
        if connection is None:
            #print "Socket Closed"
            self.opened = False
            if self.server_status_cb is not None:
                self.server_status_cb(False)


        else:
            data = self.queue.get()
            if self.server_activity_cb is not None:
                self.server_activity_cb(data)
            #print "Received Data: %s" % str(data)

    def send(self, data):
        if self.opened:
            self.sock.send(data)
        else:
            raise PrometheusServerError("Server is not connected")

    def shutdown(self):
        #print "Shutdown"
        self.sock.close()
        self.socket_thread.join()

def is_server_running():
    """
    Check to see if there is a server already running

    Opens up a socket, write "Ping" and wait for a response
    """
    client = None
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', PORT))
    except socket.error as err:
        #print "Socket Error: %s" % str(err)
        return False

    try:
        data = client.recv(MAX_READ_SIZE)
        #client.send("Does this work??")
        #print "Data Read from Host: %s" % str(data)
        client.close()
    except socket.error as err:
        #print "Is Server Running? Socket Error: %s" % str(err)
        return False

    return True
    





if __name__ == "__main__":
    print "HI"

