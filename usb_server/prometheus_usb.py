#! /usr/bin/python

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
import time
import signal
import socket
import threading
import select

import usb.core
import usb.util

from array import array as Array

from PyQt4.QtCore import *

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from defines import CYPRESS_VID
from defines import FX3_PID

from fx3_controller import FX3ControllerError
from fx3_controller import FX3Controller

def enum(*sequential, **named):
  enums = dict(zip(sequential, range(len(sequential))), **named)
  return type('Enum', (), enums)

USB_STATUS = enum ('FX3_CONNECTED',
                   'FX3_NOT_CONNECTED',
                   'FX3_PROGRAMMING_FAILED',
                   'FX3_PROGRAMMING_PASSED',
                   'BUSY',
                   'USER_APPLICATION')



class ListenThread(threading.Thread):

    def __init__(self, sock, server):
        super(ListenThread, self).__init__()
        self.sock = sock
        self.server = server

    def run(self):
        ready = True
        try:
            while ready:
                input_ready, output_list, except_list = select.select([self.sock], [], [])
                for s in input_ready:
                    print "Received an interrupt"
                    data = s.recv(512)
                    try:
                        self.server.connect_to_cypress_fx3()
                    except PrometheusUSBError, err:
                        print "Not Connected"
                        pass
                    if not data:
                        ready = False
                        return
                    continue

        except socket.error, err:
            print "Socket Error: %s" % str(err)
            ready = False

class PrometheusUSBError(Exception):
    pass

class PrometheusUSB(QObject):
    """
    Class to handle communication between the processor and host computer
    """
    def __init__(self,
                 usb_device_status_cb):
        super (PrometheusUSB, self).__init__()
        self.cypress_fx3_dev = None
        self.prometheus_dev = None
        self.usb_device_status_cb = usb_device_status_cb
        self.status = USB_STATUS.FX3_NOT_CONNECTED

        self.proc = QProcess()
        self.connect(self.proc, SIGNAL("finished(int, QProcess::ExitStatus)"),
            self.proc_finished)
        self.connect(self.proc, SIGNAL("readyReadStandardOutput()"),
            self.proc_read_stdio)
        self.connect(self.proc, SIGNAL("readyReadStandardError()"),
            self.proc_read_error)
        self.connect(self.proc, SIGNAL("error(QProcess::ProcessError)"),
            self.proc_error)
        self.connect(self.proc, SIGNAL("started()"),
            self.proc_started)

        self.proc.setWorkingDirectory(os.path.dirname(__file__))
        system_environment = self.proc.systemEnvironment()
        self.proc.setEnvironment(system_environment)
        #self.proc.setProcessEnvironment(system_environment)
        self.proc.start("python", ["idle_proc.py"])

#        self.rsock = None
#        self.wsock = None
#        self.rsock, self.wsock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
#        #self.rsock.setblocking(False)
#        #self.rsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#        #self.wsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#
#        self.notifier = QSocketNotifier(self.rsock.fileno(), QSocketNotifier.Read)
#        self.connect(self.notifier, SIGNAL("activated()"), self.notify)
#        #self.lthread = ListenThread(self.rsock, self)
#        #self.lthread.start()

        #Set up events
#        signal.signal(signal.SIGUSR1, self.user1_event)
        try:
            self.connect_to_cypress_fx3()
        except PrometheusUSBError, err:
            pass

        self.fx3 = None


    def list_usb_devices(self):
        try:
            usb_devices = usb.core.find(find_all = True)
        except usb.core.USBError, err:
            print "USB Error: %s" % str(err)
            return []
        return usb_devices

    def get_usb_device(self, vid, pid):
        dev = None
        try:
            dev = usb.core.find(idVendor=vid, idProduct=pid)
        except:
            print "USB Error: %s" % str(err)
            return None
        #Activate the device (to the control configuratio)
        if dev is None:
            self._set_status(USB_STATUS.FX3_NOT_CONNECTED)
            return
        dev.set_configuration()
        self._set_status(USB_STATUS.FX3_CONNECTED)
        return dev

    def connect_to_cypress_fx3(self):
        print "Connect to FX3"
        self.cypress_fx3_dev = None
        self.cypress_fx3_dev = self.get_usb_device(CYPRESS_VID, FX3_PID)
        if self.cypress_fx3_dev is None:
            self._set_status(USB_STATUS.FX3_NOT_CONNECTED)
            raise PrometheusUSBError("Cypress FX3 Not Found")

        self.cypress_fx3_dev.set_configuration()
        self.fx3 = FX3Controller(self.cypress_fx3_dev)
        self._set_status(USB_STATUS.FX3_CONNECTED)

    def is_connected(self):
        if self.fx3 is None:
            return False
        return True

    def user1_event(self, signal_number, frame):
        print "User 1 Event"
        self.wsock.send("\0")
        print "frame dir: %s" % str(dir(frame.f_globals))

#        try:
#            usb_devices = self.list_usb_devices()
#            self._set_status(USB_STATUS.FX3_NOT_CONNECTED)
#            #print "USB Devices: %s" % str(usb_devices)
#            self.connect_to_cypress_fx3()
#            #print "Connected to Cypress FX3"
#            self._set_status(USB_STATUS.FX3_CONNECTED)
#        except PrometheusUSBError, err:
#            self._set_status(USB_STATUS.FX3_NOT_CONNECTED)

    def download_program(self, buf):
        if self.cypress_fx3_dev is not None:
            try:
                self._set_status(USB_STATUS.BUSY)
                self.fx3.download(buf)
                self._set_status(USB_STATUS.FX3_PROGRAMMING_PASSED)
            except FX3ControllerError, err:
                self._set_status(USB_STATUS.FX3_PROGRAMMING_FAILED)
                raise PrometheusUSBError("Error Programming FX3: %s" % str(err))
        else:
            raise PrometheusUSBError("FX3 Not Connected")
        
    def reset(self):
        if dev is None:
            raise PrometheusUSBError("Error: There is no USB Device connected to reset")
        self.dev.reset()

    def _set_status(self, status):
        self.status = status
        if self.usb_device_status_cb is not None:
            self.usb_device_status_cb(self.status)

    def get_usb_status(self):
        return self.status

    def shutdown(self):
        #self.wsock.shutdown(socket.SHUT_RDWR)
        #self.wsock.close()
        #self.rsock.shutdown(socket.SHUT_RDWR)
        #self.rsock.close()
        #self.lthread.join()
        if self.proc is not None:
            self.proc.kill()
        pass

    def proc_read_stdio(self):
        text = self.proc.readAllStandardOutput().data().decode('utf8')
        print "Got something from sub proc"
        self.connect_to_cypress_fx3()

    def proc_read_error(self):
        text = self.proc.readAllStandardError().data().decode('utf8')
        print "proc read error: %s" % text

    def proc_error(self, error):

        print "proc error: %s" % str(error)

    def proc_started(self):
        print "proc started"

    def proc_finished(self, exit_code, exit_status):
        print "proc finished"


if __name__ == "__main__":
    print "Signal Test!"
    pu = PrometheusUSB()
    print "Insert and Remove a FX3 USB device and a Signal should be emitted"
    print "\tPress Enter to End the Test"
    import sys
    import select
    while True:
        try:
            select.select([sys.stdin], [], [])
            sys.exit()
        except select.error, err:
            print "Received an Error Message"

