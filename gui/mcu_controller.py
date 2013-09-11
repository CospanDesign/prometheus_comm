import sys
import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class MCUController (QWidget):

    def __init__(self, prometheus):
        super(MCUController, self).__init__(None)
        layout = QGridLayout()
        self.prometheus = prometheus

        #Add Regulator reset
        layout.addWidget(QLabel("MCU Controller"), 0, 0, 1, 2)
        #Add radio control buttons to indicate what tests to perform
        self.ping_check = QCheckBox("Ping")
        self.ping_check.setChecked(True)
        self.write_check = QCheckBox("Write")
        self.write_check.setChecked(True)
        self.read_check = QCheckBox("Read")
        self.read_check.setChecked(True)

        #Add a button to test
        write_config_button = QPushButton("Write Config")
        #self.set_background_color(write_config_button, 255, 50, 50)
        read_config_button = QPushButton("Read Config")

        test_button = QPushButton("run test")
        fpga_comm_mode = QPushButton("FPGA Comm Mode")
        proc_base_mode = QPushButton("Processor Base Mode")
        start_debug = QPushButton("Start Debug")

        layout.addWidget(self.ping_check, 1, 0, 1, 1)
        layout.addWidget(self.write_check, 2, 0, 1, 1)
        layout.addWidget(self.read_check, 3, 0, 1, 1)

        layout.addWidget(test_button, 1, 1, 1, 1)
        layout.addWidget(write_config_button, 4, 0, 1, 1)
        layout.addWidget(read_config_button, 4, 1, 1, 1)

        layout.addWidget(proc_base_mode, 5, 0, 1, 1)
        layout.addWidget(fpga_comm_mode, 5, 1, 1, 1)
        layout.addWidget(start_debug, 6, 0, 1, 2)


        self.set_background_color(self, 0, 200, 200)
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

        self.connect(write_config_button,
                     SIGNAL("clicked()"),
                     self.write_config_clicked)
        self.connect(read_config_button,
                     SIGNAL("clicked()"),
                     self.read_config_clicked)
        self.connect(start_debug,
                     SIGNAL("clicked()"),
                     self.start_debug_clicked)



    def set_background_color(self, widget, r, g, b):
        widget.setAutoFillBackground(True)
        color = QColor(r, g, b)
        p = widget.palette()
        p.setColor(widget.backgroundRole(), color)
        widget.setPalette(p)

    def test_button_clicked(self):
        self.prometheus.test_gpif_comm(
            self.ping_check.isChecked(),
            self.write_check.isChecked(),
            self.read_check.isChecked())


    def proc_base_clicked(self):
        self.prometheus.set_proc_base_mode()

    def fpga_comm_clicked(self):
        self.prometheus.set_proc_comm_mode()

    def write_config_clicked(self):
        self.prometheus.write_mcu_config(data = [0])
    
    def read_config_clicked(self):
        self.prometheus.read_mcu_config()

    def start_debug_clicked(self):
        self.prometheus.start_debug()
