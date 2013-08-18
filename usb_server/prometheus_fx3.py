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

from array import array as Array
from usb_device import USBDevice
import usb

class PrometheusFX3Error(Exception):
    pass



class PrometheusFX3(USBDevice):

    def __init__(self, usb_server):
        self.usb_server = usb_server
        super(PrometheusFX3, self).__init__()
        self.vid = 0x04B4
        self.pid = 0x0031
        self.dev = None
        self.name = "Prometheus FX3"

        self.configuration = None

    def on_connect(self):
        print "Called when a connect occurs"
        #Set up the listeners
        #self.dev.set_configuration(self.configuration)

        with self.usb_lock:
            self.add_listener(self.read_logger)
        #self.configuration = self.dev.get_active_configuration()
        #interface_number = cfg[(0,0)].bInterfaceNumber
        
    def on_release(self):
        print "Called when a release occurs"

    def read_logger(self):
        #print "Read the Logger"
        data = None
        try:
            data = self.dev.read(0x81, 128, 0, 10)
        except usb.core.USBError, err:
            if err.errno == 110:
                return
            if err.errno == 5:
                print "Device was disconnected"
                self.usb_server.update_usb()
                return 
            if err.errno == 16:
                print "Device was disconnected"
                self.usb_server.update_usb()
                return 
            else:
                print "Unknown USB Error: %s" % str(err)
                return

        #print "Read Log: %s" % str(data)
        self.usb_server.device_to_host_comm(self.name, data[0], data[8:].tostring())

    def host_to_device_comm(self, text):
        with self.usb_lock:
            try:
                self.dev.write(0x01, text, 0, 100)
            except usb.core.USBError, err:
                if err.errno == 110:
                    return
                if err.errno == 5:
                    print "Device was disconnected"
                    self.usb_server.update_usb()
                    return 
                if err.errno == 16:
                    print "Device was disconnected"
                    self.usb_server.update_usb()
                    return 




