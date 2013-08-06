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


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from processor_programmer import ProcessorProgrammer
from fpga_programmer import FPGAProgrammer

class PrometheusProgrammer (QWidget):
    """
    Visual Interface to Prometheus
    """

    def __init__(self, prometheus):
        super(PrometheusProgrammer, self).__init__(None)
        self.prometheus = prometheus
        layout = QVBoxLayout()
        self.processor_programmer = ProcessorProgrammer(self.prometheus)
        layout.addWidget(self.processor_programmer)

        self.setLayout(layout)

    def usb_connected(self):
        """
        Called when the USB device is connected
        """
        #change the background to light greend to indicate connected
        #Display 'connected on the status'
        pass

    def usb_disconnected(self):
        """
        Called when the USB device is disconnected

        Changes the background of the programmer to indicat ethat it is not
        coneccted
        """
        #Change the bakground to grey to indicate disconnected
        #Display 'disconnected on the status'
        pass

    def fpga_available(self):
        """
        Called when an FPGA is available to be programmed
        """
        pass

    def fpga_not_available(self):
        """
        Called when an FPGA is not available to be programmed
        """
        pass
