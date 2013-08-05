#! /usr/bin/python

import unittest
import sys
import os
from array import array as Array

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from usb_server import prometheus_usb as PU
from usb_server.prometheus_usb import PrometheusUSBError
from usb_server.fx3_controller import FX3Controller
from usb_server.fx3_controller import FX3ControllerError

class Test (unittest.TestCase):
    """Unit test for utils"""

    def setUp(self):
        base = os.path.join( os.path.dirname(__file__),
                             os.pardir)
        self.dbg = False

    def test_prometheus(self):
        pu = PU.PrometheusUSB()

    def test_list_devices(self):
        pu = PU.PrometheusUSB()
        usb_devices = pu.list_usb_devices()
        self.assertNotEqual(len(usb_devices), 0, "No Devices Found")
        print "USB Devices: %s" % str(usb_devices)

    def test_connect_to_cypress_fx3(self):
        pu = PU.PrometheusUSB()
        try:
            fx3 = pu.connect_to_cypress_fx3()
        except PrometheusUSBError, err:
            print "Prometheus USB Error: %s" % str(err)
            return
        print "Cypress FX3 Found"


    def test_download_fx3(self):
        pu = PU.PrometheusUSB()
        f = open("ei.img", "r")
        data = Array('B', f.read())
        f.close()
        pu.fx3 = FX3Controller(None)
        pu.cypress_fx3_dev = "Something"
        pu.download_program(data)
        pu.cypress_fx3_dev = None
        self.assertRaises(PrometheusUSBError, pu.download_program, data)
        
if __name__ == "__main__":
    unittest.main()

