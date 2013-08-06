#!/bin/bash
pid=`pidof cyusb_linux`

#Call the standard cypress controller
if [ "$pid" ]; then
    kill -s SIGUSR1 $pid
fi

pid=`pidof -x prometheus.py`
if [ "$pid" ]; then
    kill -s SIGUSR1 $pid
fi

#This is only used for debug
pid=`pidof -x prometheus_usb.py`
if [ "$pid" ]; then
    kill -s SIGUSR1 $pid
fi


