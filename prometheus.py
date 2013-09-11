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

import os
import sys
import signal
import argparse

from array import array as Array

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from gui.prometheus_gui import PrometheusGui

from server.prometheus_server import PrometheusServerError
from server.prometheus_server import PrometheusServer

from server.prometheus_client import is_server_running
from server.prometheus_client import PrometheusClientError
from server.prometheus_client import PrometheusClient
from server.prometheus_client import get_server_status
from server.prometheus_client import get_data_port
from server.prometheus_client import is_data_server_ready
from server.prometheus_client import is_usb_device_attached
from server.prometheus_client import vendor_reset_device

from usb_server.prometheus_usb import PrometheusUSBError
from usb_server.prometheus_usb import PrometheusUSBWarning
from usb_server.prometheus_usb import PrometheusUSB
from usb_server.prometheus_usb import USB_STATUS

__author__ = "dave.mccoy@cospandesign.com (Dave McCoy)"

DESCRIPTION = "\n"\
    "Prometheus controller and programmer: Standalone or Subsystem of the\n"\
    "Nysa Plugin\n"\
    "\n"\
    "Sends and receives data between the host and Prometheus\n"\
    "\n"\
    "Starts a server on the local host that can be used to program using sockets\n"

EPILOG = "\n"\
    "Examples:\n"\
    "\n"\
    "prometheus.py\n"\
    "\tStarts the visual prometheus interface\n"\
    "\n"\
    "prometheus.py --status\n"\
    "\tReturns a human readable status of:\n"\
    "\t\tstatus server\n"\
    "\t\tdata server\n"\
    "\t\tusb server\n"\
    "\n"\
    "prometheus.py --daemon\n"\
    "\tStart the GUI in background mode the socket server is the only thing\n"\
    "\tthat will be visible\n"\
    "\n"\
    "prometheus.py --program <file>\n"\
    "\tProgram prometheus then exits, if a server is already running then\n"\
    "\tconnect to it and program and then exit\n"\
    "\n"\
    "prometheus.py --vendor_reset\n"\
    "\tPerform a vendor_reset on a possible user configuration\n"\
    "\n"

SERVER_NOT_CONNECTED                    = "Not Connected"
SERVER_CONNECTED                        = "Connected"
SERVER_WAITING                          = "Waiting for User to send all Data then close connection"

USB_DEVICE_CONNECTED                    = "Device Connected"
USB_DEVICE_NOT_CONNECTED                = "Device Not Connected"
USB_BUSY                                = "USB Busy"
USB_FAILED                              = "Device Failed to Program"
USB_PROGRAMMED                          = "Device Successfully Programmed"
USB_USER_APPLICATION                    = "User Application Active"

USB_USER_PROMETHEUS_FX3_CONNECTED       = "Prometheus Device Connected"

white = '\033[0m'
gray = '\033[90m'
red = '\033[91m'
green = '\033[92m'
yellow = '\033[93m'
blue = '\033[94m'
purple = '\033[95m'
cyan = '\033[96m'

def cl_status(level = 2, text = ""):
    #if not text.endswith("\n"):
    #    text = text + "\n"

    if level == 0:
        print "%sVerbose: %s%s" % (cyan, text, white)
    elif level == 1:
        print "%sDebug: %s%s" % (green, text, white)
    elif level == 2:
        print "%sInfo: %s%s" % (white, text, white)
    elif level == 3:
        print "%sImportant: %s%s" % (blue, text, white)
    elif level == 4:
        print "%sWarning: %s%s" % (yellow, text, white)
    elif level == 5:
        print "%sError: %s%s" % (red, text, white)
    elif level == 6:
        print "%sCritical: %s%s" % (red, text, white)
    else:
        print "Unknown Level (%d) Text: %s" % (level, text)

class Prometheus(object):
    """
    """

    def __init__(self, disable_server):
        super (Prometheus, self).__init__()

        self.data_server_status    = SERVER_NOT_CONNECTED
        self.control_server_status = SERVER_NOT_CONNECTED
        self.usb_status            = USB_DEVICE_NOT_CONNECTED
        self.usb_data = ""
        self.gui = None

        self.server = None
        if not disable_server:
            self.server = PrometheusServer(self,
                                           self.data_server_status_cb,
                                           self.data_server_activity_cb,
                                           self.controller_server_status,
                                           self.controller_server_activity)

        self.usb_server = PrometheusUSB(self.usb_device_status_cb,
                                        self.device_to_host_comm)
        self.error = ""

    def init_gui(self):
        """
        Start the GUI
        """
        self.gui = PrometheusGui(self)
        self.status(2, "Initializing GUI")
        self.status(2, "Control Server: %s" % self.control_server_status)
        self.status(2, "Data Server: %s" % self.data_server_status)
        self.status(2, "USB Controller: %s" % self.usb_status)
        return self.gui

    def closeEvent(self, event):
        #print "Quit"
        self.shutdown_server()
        super(Prometheus, self).closeEvent(event)

    def send_client_program(self, file_path):
        """
        Start a client and send the program over the client

        Args:
            file_path (string): The path of the image file to send to the server

        Returns:
            (boolean)
                True: Successfully programmed the device
                False: Failed to program the device, check get_error for error
        Raises:
            Nothing
        """
        #Make sure there is a server running
        if not is_server_running():
            self.error = "Server is not running cannot send data"
            return False

        buf = ""
        try:
            self.status(3, "Openning image file: %s" % file_path)
            f = open(file_path, "r")
            buf = f.read()
            f.close()
        except IOError, err:
            self.error = str(err)
            self.status(5, "Error Opening File: %s" % self.error)
            return False

        client = PrometheusClient()
        try:
            self.status(3, "Sending data to the server")
            client.send_data(buf)
        except PrometheusClientError, err:
            self.error = str(err)
            self.status(5, "Prometheus Client Error: %s" % self.error)
            return False

        return True

    def program_fpga(self, buf):
        try:
            self.status(3, "Program FPGA with a file the size of %d" % len(buf))
            self.usb_server.download_fpga_image(buf)
        except PrometheusUSBError, err:
            self.error = str(err)
            self.status(5, "Failed to program FPGA: %s" % self.error)
            return False
        return True

    def program_mcu(self, buf):
        """
        Program a device with the given byte array

        Args:
            buf (Array of bytes): the program in the form of a buffer

        Return:
            (boolean):
                True: Successfully Programmed
                False: Failed to Programmed, check get_error for reason

        Raises:
            Nothing
        """
        try:
            self.status(3, "Programming Device over USB")
            self.usb_server.download_program(buf)
        except PrometheusUSBError, err:
            self.error = str(err)
            self.status(5, "Failed to program USB: %s" % self.error)
            return False

        return True

    def get_error(self):
        """
        Get the error in a string form, this is good for displaying it in a
        user digestible format

        Args:
            Nothing

        Return:
            (String): Error in a readable format

        Raises:
            Nothing
        """
        return self.error

    def reset_device(self):
        """
        Reset Prometheus

        Args:
            Nothing

        Return:
            (boolean):
                True: Successfully reset the device
                False: Failed to reset the device, check get_error for reason

        Raises:
            Nothing
        """
        if usb_server.is_connected():
            self.status(3, "Reset Device")
            self.usb_server.reset()
            return True

        self.error = "No USB Device to reset"
        return False

    def shutdown_server(self):
        """
        Gracefully shutdown the server
        """
        self.status(2, "Shutdown Server")
        self.usb_server.shutdown()
        if self.server:
            self.server.shutdown()

    def controller_server_status(self, connected):
        """
        Called with the status client connects or disconnects
        """
        if connected:
            self.status(2, "Connection on status socket, Check for USB Device")
            try:
                self.status(0, "looking for a USB Device")
                self.usb_server.update_usb()
            except PrometheusUSBError, err:
                self.status(5, str(err))
                return

            if self.usb_server.is_connected():
                self.status(3, "Found a USB Device")
            #print "program status is connected"
            #Send status update
            self.control_server_status = SERVER_CONNECTED
            status = self.status_string()
            if self.gui:
                self.gui.status_server_connected()
        else:
            #print "program status is disconnected"
            self.control_server_status = SERVER_NOT_CONNECTED
            self.status(1, "Status server disconnected")
            if self.gui:
                self.gui.status_server_disconnected()

        self.status(2, self.control_server_status)

    def status(self, level = 2, text = ""):
        if self.gui is None:
            print "Set Status"
            cl_status(level, text)
            return
        #print "Set GUI Status: %d, %s" % (level, text)
        self.gui.set_status(level, text)
        #print "GUI Status Set"

    def status_string(self):
        """
        Get the status of everything
        """
        status_string = ""

        status_string += "Data Server: %s\n" % self.data_server_status
        status_string += "Status Server: %s\n" % self.control_server_status
        status_string += "USB Status: %s\n" % self.usb_status
        return status_string

    def controller_server_activity(self, data):
        """
        Called when new data is received on the status server
        """
        self.sever.send_status(self.status_string())


    def data_server_status_cb(self, connected):
        """
        This is called when a client either connects or disconnects
        """
        print "Data Server Status"
        if connected:
            self.data_server_status = SERVER_CONNECTED
            self.status(3, "Client connected to data server")
            print "Server is connected"
            if self.gui:
                self.gui.data_server_connected()
            print "Updated server connected"
        else:
            self.data_server_status = SERVER_NOT_CONNECTED
            self.status(3, "Client disconnected from data server")
            print "Server is not connected"
            if self.gui:
                self.gui.data_server_disconnected()
            print "Updated server disconnected"

        self.status(2, self.data_server_status)
        #Now analyze the data that came in over the server
        print "Done with data aserver callback"

    def data_server_activity_cb(self, data):
        """
        Called when new data is received on the server
        """
        self.data_server_string = SERVER_WAITING
        #print "New Data"
        #print "%s\n" % data
        device = data.partition(":")[0]
        buf = Array('B', data.partition(":")[2])
        if device == "MCU":
            self.program_mcu(buf)
        else:
            self.program_fpga(buf)


    def usb_device_status_cb(self, status):
        #print "USB Main Callback"
        #self.status(0, "USB Device CB: %d" % status)
        if status == USB_STATUS.BOOT_FX3_CONNECTED:
            if self.usb_status != USB_DEVICE_CONNECTED:
                self.usb_status = USB_DEVICE_CONNECTED
                self.status(3, self.usb_status)
                if self.gui:
                    self.gui.usb_connected()
        elif status == USB_STATUS.DEVICE_NOT_CONNECTED:
            if self.usb_status != USB_DEVICE_NOT_CONNECTED:
                self.usb_status = USB_DEVICE_NOT_CONNECTED
                self.status(2, self.usb_status)
                if self.gui:
                    self.gui.usb_disconnected()

        elif status == USB_STATUS.FX3_PROGRAMMING_FAILED:
            if self.usb_status != USB_FAILED:
                self.usb_status = USB_FAILED
                self.status(5, self.usb_status)

        elif status == USB_STATUS.FX3_PROGRAMMING_PASSED:
            if self.usb_status != USB_PROGRAMMED:
                self.usb_status = USB_PROGRAMMED
                self.status(2, self.usb_status)

        elif status == USB_STATUS.BUSY:
            if self.usb_status != USB_BUSY:
                self.usb_status = USB_BUSY
                self.status(2, self.usb_status)

        elif status == USB_STATUS.USER_APPLICATION:
            if self.usb_status != USB_USER_APPLICATION:
                self.usb_status = USB_USER_APPLICATION
                self.status(2, self.usb_status)

        elif status == USB_STATUS.PROMETHEUS_FX3_CONNECTED:
            if self.usb_status != USB_USER_PROMETHEUS_FX3_CONNECTED:
                self.usb_status = USB_USER_PROMETHEUS_FX3_CONNECTED
                self.status(3, self.usb_status)


        #print "USB Main Callback Finished"

    def host_to_device_comm(self, text):
        #Write data to the device
        self.status(0, "Write Data to the device")
        self.usb_server.host_to_device_comm(text)
        

    def device_to_host_comm(self, name, level, text):
        #self.status(0, "Data from: %s: %s" % (name, text0))
        #self.gui.
        self.gui.comm.in_data(level, text)
               

    def vendor_reset(self, vid, pid):
        #Send a Vendor Reset to put the device back into a known configuration
        self.status(1, "Sending a vendor reset to: %04X:%04X" % (vid, pid))
        try:
            self.usb_server.vendor_reset(vid, pid)
        except PrometheusUSBWarning, warning:
            self.status(3, str(warning))
            return False
        except PrometheusUSBError, err:
            self.status(4, str(err))
            return False
        return True

    def set_proc_base_mode(self):
        self.status(4, "Set Processor Base Mode")
        if not self.usb_server.is_prometheus_connected():
            self.status(5, "Prometheus is not connected")
            return

    def set_proc_comm_mode(self):
        self.status(4, "Set Processor Comm Mode")
        if not self.usb_server.is_prometheus_connected():
            self.status(5, "Prometheus is not connected")
            return
        self.usb_server.prometheus_write_config(address = 0xB1, data = [0])

    def write_mcu_config(self, data = []):
        self.status(3, "Write %s to MCU Config" % str(data))
        if not self.usb_server.is_prometheus_connected():
            self.status(5, "Prometheus is not connected")
            return
        self.usb_server.prometheus_write_config(address = 0xB3, data = data)

    def read_mcu_config(self):
        self.status(3, "Read MCU Config Data")
        if not self.usb_server.is_prometheus_connected():
            self.status(5, "Prometheus is not connected")
            return
        self.usb_server.prometheus_read_config(address = 0xB3, length = 1)

    def test_gpif_comm(self, ping_test, read_test, write_test):
        self.status(4, "Running GPIF Test for:")
        if not (ping_test or read_test or write_test):
            self.status(5, "\tNo test specified by user!")
            return
        if ping_test:
            self.status(4, "\tPing Test")
        if read_test:
            self.status(4, "\tRead Test")
        if write_test:
            self.status(4, "\tWrite Test")

        if not self.usb_server.is_prometheus_connected():
            self.status(5, "Prometheus is not connected")
            return

    def start_debug(self):
        self.status(3, "Start MCU debug logger")
        if not self.usb_server.is_prometheus_connected():
            self.status(5, "Prometheus is not connected")
            return
        self.usb_server.prometheus_start_debug()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
        description=DESCRIPTION,
        epilog=EPILOG
    )

    global debug
    debug = False
    #Make debug global to the all modules

    #Add arguments to the parser
    parser.add_argument("-d", "--debug", action='store_true',
            help="Output test debug information")
    parser.add_argument("-ns", "--no_server", action='store_true',
            help="Disable the Socket server (Good for debugging)")
    parser.add_argument("--daemon", action="store_true",
            help="Start Prometheus comm as a daemon")
    parser.add_argument("-s", "--status", action='store_true',
            help="Returns the status of both servers and usb")
    parser.add_argument("-vr", "--vendor_reset",
            type=str,
            nargs=1,
            help="Perform a Vendor Reset on a specified VID:UID")
    parser.add_argument("-r", "--reset", action="store_true",
            help="Reset Prometheus")
    parser.add_argument("-pp", "--program_processor",
            type=str,
            nargs=1,
            help="Starts Prometheus either alone or as a client, Programs the MCU")
    parser.add_argument("-p", "--program",
            type=str,
            nargs=1,
            help="Starts Prometheus either alone or as a client, Programs the FPGA")

    parser.parse_args()
    args = parser.parse_args()
    disable_server = False

    #Check if the server socket is open

    if args.debug:
        cl_status(1, "Debug Enabled")
        debug = True

    if args.no_server:
        disable_server = True

    if args.vendor_reset:
        cl_status (0, "Perform Vendor Reset on %s" % args.vendor_reset[0])
        status = vendor_reset_device(usb_id=args.vendor_reset[0])
        cl_status (0, "Status\n%s" % status)
        sys.exit(0)

    if args.status:
        #if not is_server_running():
        #    print "Server Not Running"
        #    sys.exit(0)

        status = get_server_status()
        cl_status (0, "Status\n%s" % status)
        sys.exit(0)

    if args.daemon:
        cl_status(2, "Run the system as a deamon")
        sys.exit(0)

    if args.program:
        cl_status (3, "Program the FPGA")
        status = get_server_status()

        port = 0
        data_server_ready = False
        usb_attached = False
        try:
            port = get_data_port(status)
            data_server_ready = is_data_server_ready(status)
            usb_attached = is_usb_device_attached(status)
            cl_status(1, "Data Port: 0x%X" % port)
            if data_server_ready:
                cl_status(1, "Data Server ready")
            else:
                cl_status(1, "Data Server not ready")
                sys.exit(1)

            file_path = args.program[0]
            cl_status(3, "Openning File: %s" % file_path)
            f = open(file_path, "r")
            buf = f.read()
            pc = PrometheusClient()
            cl_status(3, "Sending Data")
            pc.send_fpga_bitfile(buf)

        except PrometheusClientError, err:
            cl_status(4, str(err))
            sys.exit(1)

        sys.exit(0)

    if args.program_processor:
        cl_status (2, "Run the system as a client")
        status = get_server_status()
        #print "status:"
        #print status
        port = 0
        data_server_ready = False
        usb_attached = False
        try:
            port = get_data_port(status)
            data_server_ready = is_data_server_ready(status)
            usb_attached = is_usb_device_attached(status)
            cl_status(1, "Data Port: 0x%X" % port)
            if data_server_ready:
                cl_status(1, "Data Server ready")
            else:
                cl_status(1, "Data Server not ready")

            if usb_attached:
                cl_status(1, "USB Device is available")
            else:
                cl_status(1, "USB Device is not available")
            file_path = args.program_processor[0]
            #print "System vars: %s" % str(dir(sys))
            #print "System path: %s" % sys.argv[0]
            #print "File Path: %s" % file_path
            f = open(file_path, "r")
            buf = f.read()
            pc = PrometheusClient()
            pc.send_mcu_firmware(buf)

        except PrometheusClientError, err:
            cl_status(4, str(err))
            sys.exit(1)
        sys.exit(0)

    #Visual Server Mode
    cl_status(0, "Starting Main GUI")
    app = QApplication(sys.argv)
    prometheus = Prometheus(disable_server)
    prometheus.init_gui()
    sys.exit(app.exec_())

