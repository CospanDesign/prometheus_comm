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

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir,
                "common"))

from common import cypress_error_translator
from mcu_controller import MCUController

class PrometheusComm (QWidget):
    """
    Visual Interface to Prometheus
    """

    def __init__(self, prometheus):
        super(PrometheusComm, self).__init__()
        self.prometheus = prometheus
        self.mcu_controller = MCUController(self.prometheus)
        layout = QVBoxLayout()
        self.comm = QTextEdit()
        self.in_command = QLineEdit()
        self.send_button = QPushButton("Send")
        layout.addWidget(QLabel("Comm"))
        layout.addWidget(self.comm)

        command_layout = QHBoxLayout()

        command_layout.addWidget(self.in_command)
        command_layout.addWidget(self.send_button)
        layout.addLayout(command_layout)

        layout.addWidget(self.mcu_controller)
        
        self.setLayout(layout)

        self.text_cursor = self.comm.textCursor()

        self.origin_format = QTextCharFormat()
        self.origin_format.setForeground(Qt.black)
        self.origin_format.setBackground(Qt.white)
        self.origin_format.setFontWeight(QFont.Bold)
        #self.origin_format.setFontUnderline(True)

        self.out_format = QTextCharFormat()
        self.out_format.setForeground(Qt.black)
        self.out_format.setBackground(Qt.white)

        self.in_format = QTextCharFormat()
        self.in_format.setForeground(Qt.black)
        self.in_format.setBackground(Qt.gray)

        #Set Format
        self.verbose_format = QTextCharFormat()
        self.verbose_format.setForeground(Qt.white)
        self.verbose_format.setBackground(Qt.black)

        self.debug_format = QTextCharFormat()
        self.debug_format.setForeground(Qt.green)
        self.debug_format.setBackground(Qt.blue)

        self.info_format = QTextCharFormat()
        self.info_format.setForeground(Qt.black)
        self.info_format.setBackground(Qt.white)

        self.important_format = QTextCharFormat()
        self.important_format.setForeground(Qt.blue)
        self.important_format.setBackground(Qt.black)

        self.warning_format = QTextCharFormat()
        self.warning_format.setForeground(Qt.yellow)
        self.warning_format.setBackground(Qt.black)

        self.error_format = QTextCharFormat()
        self.error_format.setForeground(Qt.red)
        self.error_format.setBackground(Qt.white)

        self.critical_format = QTextCharFormat()
        self.critical_format.setForeground(Qt.red)
        self.critical_format.setBackground(Qt.black)


        self.connect(self.send_button, SIGNAL("clicked()"), self.send_pressed)
        self.connect(self.in_command, SIGNAL("returnPressed()"), self.send_pressed)

    def insert_text(self, origin, text, text_format = None):
        if text_format is None:
            text_format = self.plain_format
        text = " %s" % text

        if not text.endswith("\n"):
            text += "\n"

        if origin:
            self.text_cursor.insertText("%s:" % origin, self.origin_format)
            self.comm.moveCursor(QTextCursor.End)

        self.text_cursor.insertText(text, text_format)
        verticalScroll = self.comm.verticalScrollBar()
        actualValue = verticalScroll.value()
        maxValue = verticalScroll.maximum()
        self.comm.moveCursor(QTextCursor.End)

    def out_data(self, text):
        #text = "Host: %s" % text
        self.insert_text("Host", text, self.out_format)

    def in_data(self, level, text):
        #text = "Device: %s" % text
        if "error code" in text.lower():
            #print "text: %s" % text
            lowtext = text.lower()
            length = len(lowtext.partition("error code:")[0])
            error = lowtext.partition("error code:")[2]
            error = error.strip()
            #print "Error string: %s" % error
            error_string = ""
            try:
                error = int(error, 16)
                error_string = cypress_error_translator.error_translate(error)
            except ValueError:
                error_string = "error while reading from MCU Error: %s" % str(error_string)
            except KeyError:
                error_string = "Unrecognized MCU Error: 0x%02X" % error
            text = text[0:length - 1]
            text += " " + error_string

        fmt = self.in_format
        if level == 0:
            fmt = self.verbose_format
        elif level == 1:
            fmt = self.debug_format
        elif level == 2:
            fmt = self.info_format
        elif level == 3:
            fmt = self.warning_format
        elif level == 4:
            fmt = self.error_format
        elif level == 5:
            fmt = self.critical_format

        self.insert_text("Device", text, fmt)


    def send_pressed(self):
        #print "send pressed"
        text = self.in_command.text()
        self.in_command.setText("")
        if len(text) > 0:
            self.out_data(text)
            self.prometheus.host_to_device_comm(text)

