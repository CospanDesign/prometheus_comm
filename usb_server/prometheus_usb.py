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
import signal
import time

import usb.core
import usb.util


from array import array as Array

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from defines import CYPRESS_VID
from defines import FX3_PID

from fx3_controller import FX3ControllerError
from fx3_controller import FX3Controller

class PrometheusUSBError(Exception):
    pass

class PrometheusUSB(object):
    """
    Class to handle communication between the processor and host computer
    """
    def __init__(self):
        super (PrometheusUSB, self).__init__()
        self.cypress_fx3_dev = None
        self.prometheus_dev = None
        #Set up events
        signal.signal(signal.SIGUSR1, self.user1_event)
        signal.signal(signal.SIGUSR2, self.user2_event)
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
        dev.set_configuration()
        return dev

    def connect_to_cypress_fx3(self):
        self.cypress_fx3_dev = None
        self.cypress_fx3_dev = self.get_usb_device(CYPRESS_VID, FX3_PID)
        if self.cypress_fx3_dev is None:
            raise PrometheusUSBError("Cypress FX3 Not Found")
        self.fx3 = FX3Controller(self.cypress_fx3_dev)

    def user1_event(self, signal_number, frame):
        print "User 1 Event"
        try:
            usb_devices = self.list_usb_devices()
            print "USB Devices: %s" % str(usb_devices)
            self.connect_to_cypress_fx3()
            print "Connected to Cypress FX3"
        except PrometheusUSBError, err:
            pass

    def user2_event(self, signal_number, frame):
        print "User 2 Event"

    def download_program(self, buf):
        if self.cypress_fx3_dev is not None:
            try:
                self.fx3.download(buf)
            except FX3ControllerError, err:
                raise PrometheusUSBError("Error Programming FX3: %s" % str(err))
        else:
            raise PrometheusUSBError("FX3 Not Connected")
        
    def reset(self):
        if dev is None:
            raise PrometheusUSBError("Error: There is no USB Device connected to reset")
        self.dev.reset()



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

