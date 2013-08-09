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
import time


from PyQt4.QtCore import *

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from defines import VERSION
from defines import STATUS_PORT
from defines import DATA_PORT

MAX_READ_SIZE = 1024

class SocketThread(threading.Thread):
    def __init__(self, sock, connection_cb):
        super(SocketThread, self).__init__()
        self.sock = sock
        self.rkiller, self.wkiller = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        self.connection_cb = connection_cb
        self.conn = None

    def run(self):
        while True:
            try:
                ifilelist, ofilelist, efilelist = select.select([self.sock, self.rkiller], [], [])
                if self.rkiller in ifilelist:
                    break
                self.connection_cb()
            except socket.error, err:
                print "Socket Error: %s" % str(err)
                break
            except select.error, err:
                print "Select Error: %s" % str(err)
                break

    def kill(self):
        #print "KILL BOT!!"
        #self.wkiller.sendall("HI")
        self.wkiller.shutdown(socket.SHUT_WR)
        self.wkiller.close()


class PrometheusServerError(Exception):
    pass

class PrometheusServer(QObject):
    """
    Local Socket server used to facilitate inter process communication
    """
    def __init__(self,
                 prometheus,
                 data_status_cb = None,
                 data_activity_cb = None,
                 status_connection_cb = None,
                 status_activity_cb = None):
        super (PrometheusServer, self).__init__()
        self.greeting_message = "Prometheus Server Version: %s\n\n" % VERSION

        #Get the callbacks
        self.prometheus = prometheus
        self.data_status_cb = data_status_cb
        self.data_activity_cb = data_activity_cb
        self.status_connection_cb = status_connection_cb
        self.status_activity_cb = status_activity_cb


        #Start the status server
        self.status_sock = None
        self.status_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.status_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.status_sock.bind(('localhost', STATUS_PORT))
        self.status_sock.listen(1)
        self.status_socket_thread = SocketThread(self.status_sock,
                                                 self.server_status_connection_cb)


        #Start the data server
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.data_sock.bind(('localhost', DATA_PORT))
        self.data_sock.listen(1)
        self.data_socket_thread = SocketThread(self.data_sock,
                                               self.server_data_connection_cb)

        self.status_socket_thread.start()
        self.data_socket_thread.start()

#        self.status_notifier = QSocketNotifier(self.status_sock.fileno(),
#                                               QSocketNotifier.Read,
#                                               self)
#        self.connect(self.status_notifier,
#                     SIGNAL("activated()"),
#                     self.server_status_connection_cb)
#
#        self.data_notifier = QSocketNotifier(self.data_sock.fileno(),
#                                               QSocketNotifier.Read,
#                                                self)
#        self.connect(self.data_notifier,
#                     SIGNAL("activated()"),
#                     self.server_data_connection_cb)


    def server_data_connection_cb(self):
        print "Data Server Read!"
        connection, addr = self.data_sock.accept()
        self.data_status_cb(True)
        data = ""
        while True:
            buf = connection.recv(1024)
            if len(buf) == 0:
                #We're done
                break
            else:
                #Append the data on the the buffer
                data += buf
        self.data_activity_cb(data)
        connection.shutdown(socket.SHUT_RD)
        connection.close()
        self.data_status_cb(False)
        #self.data_socket_thread = SocketThread(self.data_sock,
        #                                       self.server_data_connection_cb)
        #self.data_socket_thread.start()


    #Status Server Callback for incomming data
    def server_status_connection_cb(self):
        print "Status Server Read!"
        connection, addr = self.status_sock.accept()
        data = ""
        vid = 0
        pid = 0
        while True:
            buf = connection.recv(1024)
            if len(buf) == 0:
                #We're done
                break
            else:
                #Append the data on the the buffer
                data += buf
                print "Data: %s" % data

                if data[0] == '?':
                    print "Got a request"
                    break
                if "vr" in data:
                    print "Vendor Reset"
                    usb_string = data[2:]
                    try:
                        vid = int(usb_string.partition(":")[0], 16)
                        pid = int(usb_string.partition(":")[2], 16)
                    except ValueError, err:
                        connection.sendall("Error in the string %s, %s" % (usb_string, str(err)))
                        return


                    result = self.prometheus.vendor_reset(vid, pid)
                    if result:
                        buf = "Successfully Reset: %04X:%04X\n" % (vid, pid)
                    else:
                        buf = "Failed to Reset: %04X:%04X\n" % (vid, pid)

                    connection.sendall(buf)
                    return


        self.status_connection = connection
        self.status_connection_cb(True)
        buf = self.greeting_message
        buf += "Data Port: 0x%X\n" % DATA_PORT
        buf += self.prometheus.status_string()

        #print "Sending:"
        #print "%s" % buf
        connection.sendall(buf)
        self.status_connection_cb(False)
        connection.shutdown(socket.SHUT_WR)
        connection.close()
        #self.server_socket_thread = SocketThread(self.data_sock,
                                               #self.server_data_connection_cb)
        #self.server_socket_thread.start()


    def shutdown(self):
        #print "Server KILL"
        if self.data_socket_thread is not None:
            self.status_sock.shutdown(socket.SHUT_WR)
            self.data_socket_thread.kill()
            self.data_socket_thread.join()
            self.data_socket_thread = None

        if self.status_socket_thread is not None:
            self.status_sock.shutdown(socket.SHUT_WR)
            self.status_socket_thread.kill()
            self.status_socket_thread.join()
            self.status_socket_thread = None


