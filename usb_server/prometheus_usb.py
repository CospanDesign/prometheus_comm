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
import re
from subprocess import *

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

SLEEP_COUNT = 2

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

    def __init__(self, file_path, server):
        super(ListenThread, self).__init__()
        self.file_path = file_path
        self.server = server

    def run(self):
        file_path = '/var/log/syslog'
        self.p = Popen(['tail', '-f', file_path], stdout=PIPE)
        self.p.stdout.flush()
        start = time.time() - 100

        self.ready = True
        while self.ready:
            data = self.p.stdout.readline()
            end = time.time()
            if end - start < SLEEP_COUNT:
                continue
            if re.search("usb", data):
                time.sleep(.2)
                start = time.time()
                try:
                    self.server.update_usb()
                except PrometheusUSBError, err:
                    pass

    def kill(self):
        if self.p is not None:
            self.p.kill()
        self.ready = False

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
        try:
            self.update_usb()
        except PrometheusUSBError, err:
            pass

        self.fx3 = None
        self.listen_thread = ListenThread("/var/log/syslog", self)
        self.listen_thread.start()


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
            #self._set_status(USB_STATUS.FX3_NOT_CONNECTED)
            return
        #dev.set_configuration()
        #self._set_status(USB_STATUS.FX3_CONNECTED)
        return dev

    def update_usb(self):
        #print "Update USB"
        #Check if my current handle to the FX3 is None
        if self.cypress_fx3_dev is None:
            #if so see if the there is a FX3 device attached to the USB port
            self.cypress_fx3_dev = self.get_usb_device(CYPRESS_VID, FX3_PID)
            if self.cypress_fx3_dev is None:
                #print "\tNot Connected"
                self._set_status(USB_STATUS.FX3_NOT_CONNECTED)
                self.fx3 = None
                raise PrometheusUSBError("Cypress FX3 Not Found")
            else:
                #print "\tConnected"
                #print "Found: %X:%X" % (self.cypress_fx3_dev.idVendor, self.cypress_fx3_dev.idProduct)
                #self.cypress_fx3_dev.set_configuration()
                self.fx3 = FX3Controller(self.cypress_fx3_dev)
                self._set_status(USB_STATUS.FX3_CONNECTED)
        else:
            #Check if the fx3 chip was disconnected
            devices = self.list_usb_devices()
            for device in devices:
                #print "Checking: VID:PID %X:%X" % (device.idVendor, device.idProduct)
                if device.idVendor == CYPRESS_VID and device.idProduct == FX3_PID:
                    return

            self.cypress_fx3_dev = None
            self._set_status(USB_STATUS.FX3_NOT_CONNECTED)


    def is_connected(self):
        if self.cypress_fx3_dev is None:
            #print "Not Connected"
            return False
        #print "Connected"
        return True

    def download_program(self, buf):
        if self.cypress_fx3_dev is not None:
            try:
                self.fx3 = FX3Controller(self.cypress_fx3_dev)
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
        if self.cypress_fx3_dev is not None:
            self.cypress_fx3_dev.reset()
            self.cypress_fx3_dev = None
        self.listen_thread.kill()

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

