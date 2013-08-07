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

from defines import CONNECTED_COLOR
from defines import UNCONNECTED_COLOR

NOT_CONNECTED = "Not Connected"
CONNECTED = "Connected"

class PrometheusServerStatus (QWidget):
    """
    Visual Interface to Prometheus
    """
    def __init__(self, prometheus, name):
        super(PrometheusServerStatus, self).__init__(None)
        layout = QGridLayout()
        self.server_status = QLabel(NOT_CONNECTED)

        layout.addWidget(QLabel(name), 0, 0, 1, 1)
        layout.addWidget(self.server_status, 0, 1, 1, 1)
        self.setLayout(layout)
        self.set_background_color_tuple(UNCONNECTED_COLOR)

    def connected(self):
        self.server_status.setText(CONNECTED)
        self.set_background_color_tuple(CONNECTED_COLOR)

    def disconnected(self):
        self.server_status.setText(NOT_CONNECTED)
        self.set_background_color_tuple(UNCONNECTED_COLOR)

    def set_background_color_tuple(self, color):
        self.set_background_color(color[0], color[1], color[2])
 
    def set_background_color(self, r, g, b):
        self.setAutoFillBackground(True)
        color = QColor(r, g, b)
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)


