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

class PrometheusStatus (QWidget):
    """
    Visual Interface to Prometheus
    """

    def __init__(self, prometheus):
        super(PrometheusStatus, self).__init__()
        layout = QVBoxLayout()
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout.addWidget(QLabel("Status"))
        layout.addWidget(self.output)
        self.setLayout(layout)
        self.text_cursor = self.output.textCursor()

        self.plain_format = QTextCharFormat()
        self.plain_format.setForeground(Qt.black)
        self.plain_format.setBackground(Qt.white)
        
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

        self.warning_format = QTextCharFormat()
        self.warning_format.setForeground(Qt.yellow)
        self.warning_format.setBackground(Qt.black)

        self.error_format = QTextCharFormat()
        self.error_format.setForeground(Qt.red)
        self.error_format.setBackground(Qt.white)

        self.critical_format = QTextCharFormat()
        self.critical_format.setForeground(Qt.red)
        self.critical_format.setBackground(Qt.black)
        self.level = 0


    def set_level(self, level):
        """
        Level 0 - 5
        """
        self.level = level

    def insert_text(self, text, text_format = None):
        if text_format is None:
            text_format = self.plain_format

        if not text.endswith("\n"):
            text += "\n"
        self.text_cursor.insertText(text, text_format)
        verticalScroll = self.output.verticalScrollBar()
        actualValue = verticalScroll.value()
        maxValue = verticalScroll.maximum()
        self.output.moveCursor(QTextCursor.End)

    def verbose(self, text):
        text = "Verbose: %s" % text
        if self.level == 0:
            self.insert_text(text, self.verbose_format)

    def debug(self, text):
        text = "Debug: %s" % text
        if self.level <= 1:
            self.insert_text(text, self.debug_format)

    def info(self, text):
        text = "Info: %s" % text
        if self.level <= 2:
            self.insert_text(text, self.info_format)

    def warning(self, text):
        text = "Warning: %s" % text
        if self.level <= 3:
            self.insert_text(text, self.warning_format)

    def error(self, text):
        text = "Error: %s" % text
        if self.level <= 4:
            self.insert_text(text, self.error_format)

    def critical(self, text):
        text = "Critical: %s" % text
        self.insert_text(text, self.critical_format)

