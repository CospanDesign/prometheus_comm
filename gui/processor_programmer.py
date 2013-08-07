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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from array import array as Array

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from usb_server.prometheus_usb import PrometheusUSBError

from defines import UNCONNECTED_COLOR
from defines import CONNECTED_COLOR

class ProcessorProgrammerError(Exception):
    pass

class ProcessorProgrammer (QWidget):
    """
    Visual Interface to Prometheus
    """

    def __init__(self, prometheus):
        super(ProcessorProgrammer, self).__init__(None)
        layout = QGridLayout()
        self.prometheus = prometheus

        #Add file selector
        self.file_path = QLineEdit()
        select_proc_image_button = QPushButton("Select Processor Image")
        self.connect(select_proc_image_button,
                     SIGNAL("clicked()"),
                     self.processor_file_chooser)

        #Add processor download button
        processor_program_button = QPushButton("Program Processor")
        self.connect(processor_program_button,
                     SIGNAL("clicked()"),
                     self.processor_program_pressed)

        #Add Widgets to Layout
        layout.addWidget(QLabel("Processor Programmer"), 0, 0, 1, 4)
        layout.addWidget(QLabel("img File:"), 1, 0, 1, 1)
        layout.addWidget(self.file_path, 1, 1, 1, 2)
        layout.addWidget(select_proc_image_button, 1, 3, 1, 1)
        layout.addWidget(processor_program_button, 2, 0, 1, 4)
        #self.set_background_color(150, 150, 200)
        self.set_background_color_tuple(UNCONNECTED_COLOR)

        #Add widgets to layout
        self.setLayout(layout)

    def connected(self):
        """
        Called when the USB device is connected
        """
        #change the background to light greend to indicate connected
        #Display 'connected on the status'
        self.set_background_color_tuple(CONNECTED_COLOR)

    def disconnected(self):
        """
        Called when the USB device is disconnected

        Changes the background of the programmer to indicat ethat it is not
        coneccted
        """
        #Change the bakground to grey to indicate disconnected
        #Display 'disconnected on the status'
        self.set_background_color_tuple(UNCONNECTED_COLOR)

    def processor_file_chooser(self):
        """
        Open up the file file chooser to select a file to program
        """
        d = QFileDialog(caption="Select a FX3 Image",
                        directory = ".",
                        filter = "*.img")
        #TODO: Setup the start directory!
        text = d.getOpenFileName()
        self.file_path.setText(text)

    def processor_program_pressed(self):
        print "Processor Programmed Pressed"
        self.prometheus.status(0, "User Programming from File")
        file_path = self.file_path.text()
        buf = None
        try:
            f = open(file_path, "r")
            buf = Array('B', f.read())
            f.close()
        except IOError, err:
            raise ProcessorProgrammerError("Error Reading File: %s" % str(err))

        try:
            self.prometheus.program_device(buf)
        except PrometheusUSBError, err:
            self.prometheus.status(3, "Failed to Program USB: %s" % str(err))

    def set_background_color_tuple(self, color):
        self.set_background_color(color[0], color[1], color[2])
 
    def set_background_color(self, r, g, b):
        self.setAutoFillBackground(True)
        color = QColor(r, g, b)
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)


