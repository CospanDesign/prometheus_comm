#! /usr/bin/python

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__),
                os.pardir))

from server import prometheus_server as ps



class Test (unittest.TestCase):
    """Unit test for utils"""
 
    def setUp(self):
        base = os.path.join( os.path.dirname(__file__),
                             os.pardir)
        self.dbg = False

    def test_is_server_connected(self):
        result = ps.is_server_running()
        self.assertFalse(result)

    def test_server(self):
        self.assertFalse(ps.is_server_running(),
                         "Cannot test server, server is already running!")

        server = ps.PrometheusServer()
        result = ps.is_server_running()
        server.shutdown()
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()

