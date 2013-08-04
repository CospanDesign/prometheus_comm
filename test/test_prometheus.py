#! /usr/bin/python

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

import prometheus
from server import prometheus_server as PS

class Test (unittest.TestCase):
    """Unit test for utils"""
 
    def setUp(self):
        base = os.path.join( os.path.dirname(__file__),
                             os.pardir)
        self.dbg = False

    def test_prometheus(self):
        self.assertFalse(PS.is_server_running(), "Server is currently Running!")
        p = prometheus.Prometheus()
        self.assertTrue(PS.is_server_running())
        p.shutdown_server()
        

if __name__ == "__main__":
    unittest.main()

