import sys
import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class GPIFTester (QWidget):

    def __init__(self, prometheus):
        super(GPIFTester, self).__init__(None)
        layout = QGridLayout()
        self.prometheus = prometheus

        #Add Regulator reset
        layout.addWidget(QLabel("GPIF Tester"), 0, 0, 1, 2)
        #Add radio control buttons to indicate what tests to perform
        self.ping_check = QCheckBox("Ping")
        self.ping_check.setChecked(True)
        self.write_check = QCheckBox("Write")
        self.write_check.setChecked(True)
        self.read_check = QCheckBox("Read")
        self.read_check.setChecked(True)
        #Add a button to test
        test_button = QPushButton("run test")
        fpga_comm_mode = QPushButton("FPGA Comm Mode")
        proc_base_mode = QPushButton("Processor Base Mode")

        layout.addWidget(self.ping_check, 1, 0, 1, 2)
        layout.addWidget(self.write_check, 2, 0, 1, 2)
        layout.addWidget(self.read_check, 3, 0, 1, 2)

        layout.addWidget(test_button, 4, 0, 1, 2)
        layout.addWidget(proc_base_mode, 5, 0, 1, 2)
        layout.addWidget(fpga_comm_mode, 6, 0, 1, 2)


        self.set_background_color(0, 200, 200)
        self.setLayout(layout)

        self.connect(test_button,
                     SIGNAL("clicked()"),
                     self.test_button_clicked)

        self.connect(proc_base_mode,
                     SIGNAL("clicked()"),
                     self.proc_base_clicked)

        self.connect(fpga_comm_mode,
                     SIGNAL("clicked()"),
                     self.fpga_comm_clicked)

    def set_background_color(self, r, g, b):
        self.setAutoFillBackground(True)
        color = QColor(r, g, b)
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)

    def test_button_clicked(self):
        self.prometheus.test_gpif_comm(
            self.ping_check.isChecked(),
            self.write_check.isChecked(),
            self.read_check.isChecked())


    def proc_base_clicked(self):
        self.prometheus.set_proc_base_mode()

    def fpga_comm_clicked(self):
        self.prometheus.set_fpga_comm_mode()


