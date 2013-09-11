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
from usb_device import USBDeviceError
import time
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


    def read_mcu_config(self, address = 0xB3, length = 1):
        data = None
        with self.usb_lock:
            try:
                data = self.dev.ctrl_transfer(
                    bmRequestType   = 0xC0,     #VRequest, from the devce, Endpoint
                    bRequest        = address,  #FPGA Comm Mode
                    wValue          = 0x00,
                    wIndex          = 0x00,
                    data_or_wLength = length,
                    timeout         = 3000)   #Timeout    = 1 second

            except usb.core.USBError, err:
                if err.errno == 110:
                    raise USBDeviceError("Device Timeout set COMM Mode")
                if err.errno == 5:
                    self.usb_server.update_usb()
                    raise USBDeviceError("Device was disconnected")

                if err.errno == 16:
                    self.usb_server.update_usb()
                    raise USBDeviceError("Device was disconnected")

                else:
                    raise USBDeviceError("Unknown USB Device Error: %s" % str(err))
        return data

    def write_mcu_config(self, address = 0xB3, data = []):
        with self.usb_lock:
            try:
                data = self.dev.ctrl_transfer(
                    bmRequestType   = 0x40,     #VRequest, from the devce, Endpoint
                    bRequest        = address,  #FPGA Comm Mode
                    wValue          = 0x00,
                    wIndex          = 0x00,
                    data_or_wLength = data)
                    #data_or_wLength = data,
                    #timeout         = 1000)   #Timeout    = 1 second

            except usb.core.USBError, err:
                if err.errno == 110:
                    raise USBDeviceError("Device Timeout set COMM Mode")
                if err.errno == 5:
                    self.usb_server.update_usb()
                    raise USBDeviceError("Device was disconnected")

                if err.errno == 16:
                    self.usb_server.update_usb()
                    raise USBDeviceError("Device was disconnected")

                else:
                    raise USBDeviceError("Unknown USB Device Error: %s" % str(err))

    def set_fpga_comm_mode(self):
        with self.usb_lock:
            try:
                self.dev.ctrl_transfer(
                    bmRequestType   = 0x40,   #VRequest, To the devce, Endpoint
                    bRequest        = 0xB1,   #FPGA Comm Mode
                    wValue          = 0x00,
                    wIndex          = 0x00,
                    data_or_wLength = "",
                    timeout         = 1000)   #Timeout    = 1 second

            except usb.core.USBError, err:
                if err.errno == 110:
                    raise USBDeviceError("Device Timeout set COMM Mode")
                if err.errno == 5:
                    self.usb_server.update_usb()
                    raise USBDeviceError("Device was disconnected")

                if err.errno == 16:
                    self.usb_server.update_usb()
                    raise USBDeviceError("Device was disconnected")

                else:
                    raise USBDeviceError("Unknown USB Device Error: %s" % str(err))


    def upload_fpga_image(self, bit_buf):
        max_size = 512
        if self.dev is None:
            raise USBDeviceError("Device is None")

        bit_buf_length = len(bit_buf)
        length_buf = Array('B', [0, 0, 0, 0])
        length_buf[3] = (bit_buf_length >> 24)  & 0x000000FF
        length_buf[2] = (bit_buf_length >> 16)  & 0x000000FF
        length_buf[1] = (bit_buf_length >> 8)   & 0x000000FF
        length_buf[0] = (bit_buf_length)        & 0x000000FF

        print "bit buf packets [3] [2] [1] [0]: %X %X %X %X" % (length_buf[3],
                                                                length_buf[2],
                                                                length_buf[1],
                                                                length_buf[0])

        print "Length: (Hex): 0x%08X, (Dec): %d" % (bit_buf_length, bit_buf_length)

        with self.usb_lock:
            try:
                self.dev.ctrl_transfer(
                    bmRequestType   = 0x40,   #VRequest, To the devce, Endpoint
                    bRequest        = 0xB2,   #FPGA Configuration mode
                    wValue          = 0x00,
                    wIndex          = 0x00,
                    data_or_wLength = length_buf.tostring(),
                    timeout         = 1000)   #Timeout    = 1 second
            except usb.core.USBError, err:
                if err.errno == 110:
                    raise USBDeviceError("Device Timed Out while attempting to send FPGA Config")
                if err.errno == 5:
                    self.usb_server.update_usb()
                    raise USBDeviceError("Device was disconnected")

                if err.errno == 16:
                    self.usb_server.update_usb()
                    raise USBDeviceError("Device was disconnected")

                else:
                    raise USBDeviceError("Unknown USB Device Error: %s" % str(err))

        print "Sleep for a few seconds" 
        time.sleep(1)

        count = 0
        with self.usb_lock:

            while len(bit_buf) > max_size:
                print "Sending: %d" % count
                count += 1

                buf = bit_buf[:max_size]
                bit_buf = bit_buf[max_size:]
                print "Length of buffer: %d" % len(buf)

                try:
                    self.dev.write(0x02, buf, 0, timeout=3000)
                    #self.dev.write(0x02, bit_buf, 0, timeout=3000)
                except usb.core.USBError, err:
                    if err.errno == 110:
                        raise USBDeviceError("Device timed out while attempting to send FPGA Config")
                    if err.errno == 5:
                        self.usb_server.update_usb()
                        raise USBDeviceError("Device was disconnected")
                
                    if err.errno == 16:
                        self.usb_server.update_usb()
                        raise USBDeviceError("Device was disconnected")
                
                    else:
                        raise USBDeviceError("Unknown USB Device Error: %s" % str(err))

            print "FPGA Data Sent"

            
            if len(bit_buf) > 0:
                try:
                    self.dev.write(0x02, bit_buf, 0, timeout=3000)
                except usb.core.USBError, err:
                    if err.errno == 110:
                        raise USBDeviceError("Device timed out while attempting to send FPGA Config")
                    if err.errno == 5:
                        self.usb_server.update_usb()
                        raise USBDeviceError("Device was disconnected")
                
                    if err.errno == 16:
                        self.usb_server.update_usb()
                        raise USBDeviceError("Device was disconnected")
                
                    else:
                        raise USBDeviceError("Unknown USB Device Error: %s" % str(err))



