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
import pyudev
from pyudev.pyqt4 import MonitorObserver

import usb.core
import usb.util

from array import array as Array

from PyQt4.QtCore import *

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from defines import CYPRESS_VID
from defines import FX3_PID

from usb_device import USBDeviceError
from usb_device import USBDevice

from boot_fx3 import BootFX3Error
from boot_fx3 import BootFX3

from prometheus_fx3 import PrometheusFX3Error
from prometheus_fx3 import PrometheusFX3

SLEEP_COUNT = 2

def enum(*sequential, **named):
  enums = dict(zip(sequential, range(len(sequential))), **named)
  return type('Enum', (), enums)

USB_STATUS = enum ('BOOT_FX3_CONNECTED',
                   'DEVICE_NOT_CONNECTED',
                   'PROMETHEUS_FX3_CONNECTED',
                   'FX3_PROGRAMMING_FAILED',
                   'FX3_PROGRAMMING_PASSED',
                   'BUSY',
                   'USER_APPLICATION')

class DelayThread(threading.Thread):
    def __init__(self, server, timeout = 2):
        super(DelayThread, self).__init__()
        self.timeout = timeout
        self.lock = threading.Lock()
        self.server = server

    def run(self):
        time.sleep(self.timeout)
        try:
            if self.lock.acquire(False):
                #print "Got a lock"
                self.server.update_usb()
            else:
                self.server.delay_cleanup()
                return

        except PrometheusUSBError, err:
            pass
        finally:
            #print "Release the lock"
            self.lock.release()
            self.server.delay_cleanup()

class PrometheusUSBError(Exception):
    pass

class PrometheusUSBWarning(Exception):
    pass

class PrometheusUSB(QObject):
    """
    Class to handle communication between the processor and host computer
    """
    def __init__(self,
                 usb_device_status_cb,
                 device_to_host_comm_cb):
        super (PrometheusUSB, self).__init__()


        self.cypress_fx3_dev = None
        self.prometheus_dev = None

        self.usb_device_status_cb = usb_device_status_cb
        self.device_to_host_comm_cb = device_to_host_comm_cb
        self.status = USB_STATUS.DEVICE_NOT_CONNECTED

        self.boot_fx3 = BootFX3()
        self.prometheus_fx3 = PrometheusFX3(self)
        self.delay_thread = None

        try:
            self.update_usb()
        except PrometheusUSBError, err:
            pass

        #pyudev
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem="usb")
        self.observer = MonitorObserver(self.monitor)
        self.observer.deviceEvent.connect(self.udev_device_event)
        print "Starting Udev monitor"
        self.monitor.start()
        #end pyudev

        self.lock = threading.Lock()

    def udev_device_event(self, device):
        try:
            vendor_id = int(device["ID_VENDOR_ID"], 16)
            product_id = int(device["ID_MODEL_ID"], 16)
            #print "vendor id: %04X" % vendor_id
            #print "product id: %04X" % product_id
            if ((vendor_id == self.boot_fx3.get_vid()) and
                (product_id == self.boot_fx3.get_pid())):
                print "Boot FX3: %s" % device.action
                if device.action == "add" or device.action == "remove":
                    self.update_usb()
            
            if ((vendor_id == self.prometheus_fx3.get_vid()) and
                (product_id == self.prometheus_fx3.get_pid())):
                print "Prometheus FX3: %s" % device.action
                if device.action == "add" or device.action == "remove":
                    self.update_usb()
            
            if ((vendor_id == 0x0403) and
                (product_id == 0x8530)):
                print "Dionysus: %s" % device.action
                if device.action == "add" or device.action == "remove":
                    self.update_usb()

        except KeyError, err:
            pass

    def update_usb(self):
        boot_vid = self.boot_fx3.get_vid()
        boot_pid = self.boot_fx3.get_pid()
        #print "Boot VID:PID %04X:%04X" % (boot_vid, boot_pid)

        p_vid = self.prometheus_fx3.get_vid()
        p_pid = self.prometheus_fx3.get_pid()
        #print "Prometheus VID:PID %04X:%04X" % (p_vid, p_pid)

        devices = usb.core.find(find_all = True)
        for device in devices:
            #print "Scanning: %04X:%04X" % (device.idVendor, device.idProduct)

            if device.idVendor == boot_vid and device.idProduct == boot_pid:
                if self.boot_fx3.is_connected():
                    self.prometheus_fx3.release()
                    print "Boot Device Attached"
                    return
                else:
                    try:
                        self.prometheus_fx3.release()
                        self.boot_fx3.connect()
                        self._set_status(USB_STATUS.BOOT_FX3_CONNECTED)
                    except BootFX3Error, err:
                        self._set_status(USB_STATUS.DEVICE_NOT_CONNECTED)
                        raise PrometheusUSBError(str(err))
                    except USBDeviceError, err:
                        self._set_status(USB_STATUS.DEVICE_NOT_CONNECTED)
                        raise PrometheusUSBError(str(err))
                    except usb.core.USBError, err:
                        self._set_status(USB_STATUS.DEVICE_NOT_CONNECTED)
                        raise PrometheusUSBError(str(err))
                    #Set Status
                    return

            if device.idVendor == p_vid and device.idProduct == p_pid:
                if self.prometheus_fx3.is_connected():
                    self.boot_fx3.release()
                    print "Prometheus FX3 is attached"
                    return
                else:
                    print "Not Connected to FX3, attempting to connect"
                    try:
                        self.boot_fx3.release()
                        self.prometheus_fx3.connect()
                        self._set_status(USB_STATUS.PROMETHEUS_FX3_CONNECTED)
                    except PrometheusFX3Error, err:
                        self._set_status(USB_STATUS.DEVICE_NOT_CONNECTED)
                        raise PrometheusUSBError(str(err))
                    except USBDeviceError, err:
                        self._set_status(USB_STATUS.DEVICE_NOT_CONNECTED)
                        raise PrometheusUSBError(str(err))
                    except usb.core.USBError, err:
                        self._set_status(USB_STATUS.DEVICE_NOT_CONNECTED)
                        raise PrometheusUSBError(str(err))
                    #Set Status
                    return


        #self.boot_fx3.release()
        #self.prometheus_fx3.release()
        #self._set_status(USB_STATUS.DEVICE_NOT_CONNECTED)

    def is_connected(self):
        if self.prometheus_fx3.is_connected() or self.boot_fx3.is_connected():
            return True
        return False

    def is_prometheus_connected(self):
        return self.prometheus_fx3.is_connected()

    def download_fpga_image(self, buf):
        if self.prometheus_fx3.is_connected():
            self.prometheus_fx3.upload_fpga_image(buf)
        else:
            raise PrometheusUSBError("FX3 Not Connected")

    def download_program(self, buf):
        if self.boot_fx3.is_connected():
            try:
                self.boot_fx3.download(buf)
                self.boot_fx3.release()
                self._set_status(USB_STATUS.FX3_PROGRAMMING_PASSED)
                self.delay_start()
            except BootFX3Error, err:
                self._set_status(USB_STATUS.FX3_PROGRAMMING_FAILED)
                raise PrometheusUSBError("Error Programming FX3: %s" % str(err))
        else:
            raise PrometheusUSBError("FX3 Not Connected")

    def vendor_reset(self, vid, pid):
        if self.prometheus_fx3.is_connected():
            self.prometheus_fx3.reset_to_boot()
            self._set_status(USB_STATUS.DEVICE_NOT_CONNECTED)
            #print "Delay a usb scan for a couple of seconds"
            self.delay_start(timeout = 4)
            return True
        return False

    def _set_status(self, status):
        self.status = status
        if self.usb_device_status_cb is not None:
            self.usb_device_status_cb(self.status)

    def get_usb_status(self):
        return self.status

    def delay_start(self, timeout = 2):
        if self.delay_thread is None:
            self.delay_thread = DelayThread(self, timeout)
            self.delay_thread.start()

    def delay_cleanup(self):
        self.delay_thread = None

    def host_to_device_comm(self, text):
        if self.prometheus_fx3:
            self.prometheus_fx3.host_to_device_comm(text)

    def device_to_host_comm(self, name, level, text):
        self.device_to_host_comm_cb(name, level, text)


    def prometheus_read_config(self, address = 0xB3, length = 1):
        return self.prometheus_fx3.read_mcu_config(address, length)

    def prometheus_write_config(self, address = 0xB3, data = []):
        self.prometheus_fx3.write_mcu_config(address, data)

    def prometheus_start_debug(self):
        self.prometheus_fx3.write_mcu_config(address = 0xB0, data = [0])

    def shutdown(self):
        if self.cypress_fx3_dev is not None:
            self.cypress_fx3_dev.reset()
            self.cypress_fx3_dev = None
        if self.prometheus_fx3:
            self.prometheus_fx3.shutdown()







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

