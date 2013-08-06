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
import signal


sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from defines import VERSION
from defines import STATUS_PORT
from defines import DATA_PORT

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

        #signal.signal(signal.SIGUSR2, self.user2_event)

    #def user2_event(self, signal_number, frame):
    #    print "User 2 Event"

    def run(self):
        self.sock.bind(('', self.listen_port))
        while True:
            conn = None
            addr = ""
            try:
                self.sock.listen(1)
                
                conn, addr = self.sock.accept()
                print "Connected by: %s" % str(addr)
                self.connection_cb(conn)
                ready = True
                
                while ready:
                    try:
                        input_ready, output_list, except_list = select.select([conn], [], [])
                        
                        for s in input_ready:
                            data = s.recv(MAX_READ_SIZE)
                            if not data:
                                print "Closed Connection"
                                conn.shutdown(socket.SHUT_RDWR)
                                conn.close()
                                self.activity_cb(None)
                                ready = False
                                break
                            else:
                                #print "Received Data"
                                if self.queue is not None:
                                    self.queue.put(data)
                                if self.activity_cb is not None:
                                    self.activity_cb(conn)

                    except select.error, err:
                        print "Select Error"
                        break

            except socket.error, err:
                #print "Socket Error: %s" % str(err)
                return

class PrometheusServerError(Exception):
    pass

class PrometheusServer(object):
    """
    Local Socket server used to facilitate inter process communication
    """
    def __init__(self,
                 data_status_cb = None,
                 data_activity_cb = None,
                 status_connection_cb = None,
                 status_activity_cb = None):
        super (PrometheusServer, self).__init__()
        self.greeting_message = "Prometheus Server Version: %s" % VERSION

        #Get the callbacks
        self.data_status_cb = data_status_cb
        self.data_activity_cb = data_activity_cb
        self.status_connection_cb = status_connection_cb
        self.status_activity_cb = status_activity_cb


        #Start the status server
        self.status_queue = Queue.Queue()
        self.status_connection = None
        self.status_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.status_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.status_socket_thread = SocketThread(self.status_sock,
                                                 STATUS_PORT,
                                                 self.status_queue,
                                                 self.server_status_connection_cb,
                                                 self.server_status_activity_cb)



        #Start the data server
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_connection = None
        self.data_queue = Queue.Queue()
        #SO_REUSADDR is nice because if there is a mistake I'm not stuck waiting
        #For the socket to time out
        self.data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.data_socket_thread = SocketThread(self.data_sock,
                                               DATA_PORT,
                                               self.data_queue,
                                               self.server_data_connection_cb,
                                               self.server_data_activity_cb)

        self.status_socket_thread.start()
        self.data_socket_thread.start()


    def send_greeting(self, connection):
        #Send greeting
        connection.sendall(self.greeting_message)

    def server_data_connection_cb(self, connection):
        #self.send_greeting(connection)
        self.send("Ready")
        self.data_connection = connection
        if self.data_status_cb is not None:
            self.data_status_cb(True)

    #Data Server Callback for incomming data
    def server_data_activity_cb(self, connection):
        if connection is None:
            #print "Socket Closed"
            self.data_connection = None
            if self.data_status_cb is not None:
                self.data_status_cb(False)
        else:
            data = self.data_queue.get()
            if self.data_activity_cb is not None:
                self.data_activity_cb(data)
            #print "Received Data: %s" % str(data)

    def send(self, data):
        if self.data_connection:
            self.data_sock.sendall(data)
        else:
            raise PrometheusServerError("Server is not connected")

    #Status Server Callback for incomming data
    def server_status_connection_cb(self, connection):
        print "Status Connected"
        self.status_connection = connection

        if self.status_connection_cb:
            self.status_connection_cb(connection)

    def server_status_activity_cb(self, connection):
        print "New data on the status queue"
        if connection is None:
            #Socket Closed
            self.status_connection = None
            if self.status_connection_cb:
                self.status_connection_cb(False)
        else:
            data = self.data_queue.get()
            if self.status_activity_cb is not None:
                self.status_activity_cb(data)

    def send_status(self, main_status):
        print "Send status of a build"
        status = self.greeting_message
        status += " Data Port: 0x%X\n" % DATA_PORT
        status += main_status

        if self.status_connection is not None:
            self.status_connection.sendall(status)
        else:
            raise PrometheusServerError("Status Server is not connected")


    def shutdown(self):
        #print "Shutdown Servers"
        #Shutdown Data socket
        if self.data_connection is not None:
            self.data_connection.shutdown(socket.SHUT_RDWR)
            self.data_connection.close()
            self.data_connection = None

        #print "Closed Data Connection Socket"

        if self.data_sock is not None:
            self.data_sock.shutdown(socket.SHUT_RDWR)
            self.data_sock.close()
            self.data_sock = None

        #print "Closed Data Server Socket"

        if self.data_socket_thread is not None:
            self.data_socket_thread.join()
            self.data_socket_thread = None

        #print "Data Server Thread Shutdown"

        #Shutdown status socket
        if self.status_connection is not None:
            self.status_connection.shutdown(socket.SHUT_RDWR)
            self.status_connection.close()
            self.status_connection = None

        #print "Closed Status Connection Socket"

        if self.status_sock is not None:
            self.status_sock.shutdown(socket.SHUT_RDWR)
            self.status_sock.close()
            self.status_socket = None

        #print "Closed Status Server Socket"

        if self.status_socket_thread is not None:
            self.status_socket_thread.join()
            self.status_socket_thread = None

        #print "Status Server Thread Shutdown"

        #print "Both Servers are shutdown"


