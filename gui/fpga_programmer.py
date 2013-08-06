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

class FPGAProgrammer (QWidget):
    """
    Visual Interface to Prometheus
    """

    def __init__(self, prometheus):
        super(FPGAProgrammer, self).__init__(None)
        layout = QGridLayout()
        self.prometheus = prometheus

        #Add file selector
        self.file_path = QLineEdit()
        select_fpga_image_button = QPushButton("Select FPGA Image")
        self.connect(select_fpga_image_button,
                     SIGNAL("clicked()"),
                     self.fpga_file_chooser)

        #Add fpga download button
        fpga_program_button = QPushButton("Program FPGA")
        self.connect(fpga_program_button,
                     SIGNAL("clicked()"),
                     self.fpga_program_pressed)

        #Add Widgets to Layout
        layout.addWidget(QLabel("FPGA Programmer"), 0, 0, 1, 4)
        layout.addWidget(QLabel("Bit File:"), 1, 0, 1, 1)
        layout.addWidget(self.file_path, 1, 1, 1, 2)
        layout.addWidget(select_fpga_image_button, 1, 3, 1, 1)
        layout.addWidget(fpga_program_button, 2, 0, 1, 4)
        self.set_background_color(150, 150, 200)

        #Add widgets to layout
        self.setLayout(layout)

    def connected(self):
        """
        Called when the USB device is connected
        """
        #change the background to light greend to indicate connected
        #Display 'connected on the status'
        self.set_background_color(0, 200, 100)

    def disconnected(self):
        """
        Called when the USB device is disconnected

        Changes the background of the programmer to indicat ethat it is not
        coneccted
        """
        #Change the bakground to grey to indicate disconnected
        #Display 'disconnected on the status'
        self.set_background_color(150, 150, 200)

    def fpga_file_chooser(self):
        """
        Open up the file file chooser to select a file to program
        """
        d = QFileDialog(caption="Select a FX3 Image",
                        directory = ".",
                        filter = "*.bit")
        #TODO: Setup the start directory!
        text = d.getOpenFileName()
        self.file_path.setText(text)

    def set_background_color(self, r, g, b):
        self.setAutoFillBackground(True)
        color = QColor(r, g, b)
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)


