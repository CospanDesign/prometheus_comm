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

from prometheus_programmer import PrometheusProgrammer
from prometheus_status import PrometheusStatus
from prometheus_server_status import PrometheusServerStatus

from prometheus_comm import PrometheusComm

class PrometheusGui (QWidget):
    """
    Visual Interface to Prometheus
    """

    def __init__(self, prometheus):
        super(PrometheusGui, self).__init__(None)

        self.prometheus = prometheus
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle("Prometheus FX3 Server/Programmer")
        self.show()

        #Setup the main horizontal splitter
        layout = QHBoxLayout()

        #Setup the 3 status boxes on the left
        status_layout = QVBoxLayout()
        self.programmer = PrometheusProgrammer(self.prometheus)
        self.status = PrometheusStatus(self.prometheus)
        self.server_status = PrometheusServerStatus(self.prometheus)

        status_layout.addWidget(self.status)
        status_layout.addWidget(self.programmer)
        status_layout.addWidget(self.server_status)

        layout.addItem(status_layout)

        #Setup the main status box
        self.comm = PrometheusComm(self.prometheus)
        layout.addWidget(self.comm)

        self.setLayout(layout)
        self.status.set_level(0)
        #self.status.insert_text("HI")
        #self.status.verbose("HI")
        #self.status.debug("HI")
        #self.status.info("HI")
        #self.status.warning("HI")
        #self.status.error("HI")
        #self.status.critical("HI")


    def closeEvent(self, event):
        self.prometheus.shutdown_server()
        super(PrometheusGui, self).closeEvent(event)

    def set_status(self, level, text):
        if level == 0:
            self.status.verbose(text)
        elif level == 1:
            self.status.debug(text)
        elif level == 2:
            self.status.info(text)
        elif level == 3:
            self.status.warning(text)
        elif level == 4:
            self.status.error(text)
        elif level == 5:
            self.status.critical(text)
        else:
            utext = "Unknown Level (%d) Text: %s" % (level, text)
            self.status.insert_text(utext)




