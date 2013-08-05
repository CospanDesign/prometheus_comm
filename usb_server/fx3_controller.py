# -*- coding: UTF-8 -*-

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

import time
from array import array as Array
import usb.core
import usb.util



class FX3ControllerError(Exception):
    pass

class FX3Controller(object):
    def __init__(self, dev):
        super(FX3Controller, self).__init__()
        self.dev = dev

    def download(self, buf):
        """
        Download code to the FX3

        Arg:
            (Array Unsigned Bytes) An Array of unsigned bytes from the input
            file

        Returns:
            Nothing

        Raises:
            FX3ControllerError with a description of the error
        """
        pos = 0
        cyp_id = "%c%c" % (buf[0], buf[1])
        image_cntrl = buf[2]
        image_type = buf[3]
        pos = 4
        checksum = 0
        program_entry = 0x00


        print "cyp id: %s" % cyp_id
        if cyp_id != "CY":
            raise FX3ControllerError("Image file does not start with Cypress ID: %s" % cpy_id)
        print "Image Control: 0x%X" % image_cntrl
        if image_cntrl & 0x01 != 0:
            raise FX3ControllerError("Image Control Byte bit 0 != 1, thie file does not contain executable code")
        print "Image Type: 0x%X" % image_type
        if image_type != 0xB0:
            raise FX3ControllerError("Not a normal FW Binary with Checksum")

        while True:
            size = (buf[pos + 3] << 24) + (buf[pos + 2] << 16) + (buf[pos + 1] << 8) + buf[pos]
            pos += 4
            address = (buf[pos + 3] << 24) + (buf[pos + 2] << 16) + (buf[pos + 1] << 8) + buf[pos]
            pos += 4

            if size > 0:
                #print "size: 0x%X" % size
                #print "address: 0x%X" % address
                data = buf[pos: (pos + size * 4)]
                self.write_program_data(address, data)
                for i in range(0, (size * 4), 4):
                    checksum += ((data[i + 3] << 24) + (data[i + 2] << 16) + (data[i + 1] << 8) + (data[i]))
                    checksum = checksum & 0xFFFFFFFF
                pos += (size * 4)
            else:
                #print "Starting address: 0x%X" % address
                program_entry = address
                break


        read_checksum = (buf[pos + 3] << 24) + (buf[pos + 2] << 16) + (buf[pos + 1] << 8) + buf[pos]
        #print "Checksum from file: 0x%X" % read_checksum
        #print "Checksum from calculation: 0x%X" % checksum
        if read_checksum != checksum:
            raise FX3ControllerError("Checksum from file != Checksum from Data: 0x%X != 0x%X" % (read_checksum, checksum))

        time.sleep(1)
        #Set the program entry point
        write_len = self.dev.ctrl_transfer(0x40, #Vendor Request, To the devce, Endpoint
                                           0xA0, #Vendor Specific
                                           program_entry,   #Entry point of the program
                                           0)    #No data

    def write_program_data(self, address, data):
        print "Write data to the device"
        buf = Array('B', [])

        index = 0
        #Size is maximum of 4096
        finished = False
        while True:
            if len(data[index:]) > 4096:
                buf = data[index: index+ 4096]
            else:
                buf = data[index:]

            write_len = self.dev.ctrl_transfer(0x40,    #Vendor Request, to the device, endpoint
                                               0xA0,    #Vendor Spcific write command
                                               address, #Address to write
                                               data)    #Data to write

            #Check if there was an error in the transfer
            if write_len != len(buf):
                raise FX3ControllerError("Write Size != Length of buffer")

            #Update the index
            index += write_len
            address += write_len

            #Check if we wrote all the data out
            if index + write_len == len(data):
                #We're done
                break



