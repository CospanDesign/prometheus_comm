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

from usb_server.prometheus_usb import PrometheusUSBError
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
    "\tconnect to it and program and then exit\n"

SERVER_NOT_CONNECTED     = "Not Connected"
SERVER_CONNECTED         = "Connected"
SERVER_WAITING           = "Waiting for User to send all Data then close connection"

USB_DEVICE_CONNECTED     = "Device Connected"
USB_DEVICE_NOT_CONNECTED = "Device Not Connected"
USB_BUSY                 = "USB Busy"
USB_FAILED               = "Device Failed to Program"
USB_PROGRAMMED           = "Device Successfully Programmed"
USB_USER_APPLICATION     = "User Application Active"

white = '\033[0m'
gray = '\033[90m'
red = '\033[91m'
green = '\033[92m'
yellow = '\033[93m'
blue = '\033[94m'
purple = '\033[95m'
cyan = '\033[96m'

def cl_status(level = 2, text = ""):
    if not text.endswith("\n"):
        text = text + "\n"
    if level == 0:
        print "%sVerbose: %s%s" % (cyan, text, white)
    elif level == 1:
        print "%sDebug: %s%s" % (green, text, white)
    elif level == 2:
        print "%sInfo: %s%s" % (white, text, white)
    elif level == 3:
        print "%sWarning: %s%s" % (yello, text, white)
    elif level == 4:
        print "%sError: %s%s" % (red, text, white)
    elif level == 5:
        print "%sCritical: %s%s" % (red, text, white)
    else:
        utext = "Unknown Level (%d) Text: %s" % (level, text)
        print utext

def user1_event(signal_number, frame):
    print "Hello"

class Prometheus(object):
    """
    """

    def __init__(self):
        super (Prometheus, self).__init__()

        self.data_server_status    = SERVER_NOT_CONNECTED
        self.control_server_status = SERVER_NOT_CONNECTED
        self.usb_status            = USB_DEVICE_NOT_CONNECTED
        self.usb_data = ""
        self.gui = None

        self.server = PrometheusServer(self.data_server_status,
                                       self.data_server_activity,
                                       self.controller_server_status,
                                       self.controller_server_activity)

        self.usb_server = PrometheusUSB(self.usb_device_status_cb)
        self.error = ""
        self.program_buffer = Array('B', [])

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
            self.status(4, "Error Opening File: %s" % self.error)
            return False

        client = PrometheusClient()
        try:
            self.status(3, "Sending data to the server")
            client.send_data(buf)
        except PrometheusClientError, err:
            self.error = str(err)
            self.status(4, "Prometheus Client Error: %s" % self.error)
            return False

        return True

    def program_device(self, buf):
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
            self.status(2, "Programming Device over USB")
            self.usb_server.download_program(buf)
        except PrometheusUSBError, err:
            self.error = str(err)
            self.status(4, "Failed to program USB: %s" % self.error)
            return False

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
            self.status(2, "Reset Device")
            self.usb_server.reset()
            return True

        self.error = "No USB Device to reset"
        return False

    def shutdown_server(self):
        """
        Gracefully shutdown the server
        """
        self.usb_server.shutdown()
        self.status(2, "Shutdown Server")
        self.server.shutdown()

    def controller_server_status(self, connected):
        """
        Called with the status client connects or disconnects
        """
        if connected:
            #print "program status is connected"
            #Send status update
            self.control_server_status = SERVER_CONNECTED
            status = self.status_string()
            self.server.send_status(status)
        else:
            #print "program status is disconnected"
            self.control_server_status = SERVER_NOT_CONNECTED

        self.status(2, control_server_status)

    def status(self, level = 2, text = ""):
        if self.gui is None:
            cl_status(level, text)
            return
        self.gui.set_status(level, text)

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


    def data_server_status(self, connected):
        """
        This is called when a client either connects or disconnects
        """
        if connected is not None:
            print "Server is connected"
            self.data_server_status = SERVER_CONNECTED
        else:
            print "Server is not connected"
            self.data_server_status = SERVER_NOT_CONNECTED

        self.status(2, self.data_server_status)
        #Now analyze the data that came in over the server

    def data_server_activity(self, data):
        """
        Called when new data is received on the server
        """
        self.data_server_string = SERVER_WAITING
        print "New Data"
        print "%s\n" % data


    def usb_device_status_cb(self, status):
        #print "USB Main Callback"
        #self.status(0, "USB Device CB: %d" % status)
        if status == USB_STATUS.FX3_CONNECTED:
            if self.usb_status != USB_DEVICE_CONNECTED:
                self.usb_status = USB_DEVICE_CONNECTED
                self.status(2, self.usb_status)
                if self.gui:
                    self.gui.usb_connected()
        elif status == USB_STATUS.FX3_NOT_CONNECTED:
            if self.usb_status != USB_DEVICE_NOT_CONNECTED:
                self.usb_status = USB_DEVICE_NOT_CONNECTED
                self.status(2, self.usb_status)
                if self.gui:
                    self.gui.usb_disconnected()
        elif status == USB_STATUS.FX3_PROGRAMMING_FAILED:
            if self.usb_status != USB_FAILED:
                self.usb_status = USB_FAILED
                self.status(4, self.usb_status)
        elif status == USB_STATUS.FX3_PROGRAMMING_PASSED:
            if self.usb_status != USB_PROGRAMMED:
                self.usb_status = USB_PROGRAMMED
                self.status(2, self.usb_status)
        elif status == USB_STATUS.BUSY:
            if self.usb_status != USB_BUSY:
                self.usb_status = USB_BUSY
                self.status(3, self.usb_status)
        elif status == USB_STATUS.USER_APPLICATION:
            if self.usb_status != USB_USER_APPLICATION:
                self.usb_status = USB_USER_APPLICATION
                self.status(2, self.usb_status)
        #print "USB Main Callback Finished"

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
    parser.add_argument("--daemon", action="store_true",
            help="Start Prometheus comm as a daemon")
    parser.add_argument("-s", "--status", action='store_true',
            help="Returns the status of both servers and usb")
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

    #Check if the server socket is open

    if args.debug:
        cl_status(1, "Debug Enabled")
        debug = True

    if args.status:
        #if not is_server_running():
        #    print "Server Not Running"
        #    sys.exit(0)

        status = get_server_status()
        cl_status ("Status\n%s" % status)
        sys.exit(0)


    if args.daemon:
        cl_status("Run the system as a deamon")
        sys.exit(0)

    if args.program:
        cl_status ("Run the system as a client\n")
        cl_status ("\tAttempts to locate a pre-existing server")
        cl_status ("\tIf none is available then starts a server, then connect to it")
        sys.exit(0)

    if args.program_processor:
        cl_status ("Run the system as a client\n")
        cl_status ("\tAttempts to locate a pre-existing server")
        cl_status ("\tIf none is available then starts a server, then connect to it")
        sys.exit(0)


    signal.signal(signal.SIGUSR1, user1_event)

    #Visual Server Mode
    cl_status(0, "Starting Main GUI")
    app = QApplication(sys.argv)
    prometheus = Prometheus()
    prometheus.init_gui()
    sys.exit(app.exec_())

