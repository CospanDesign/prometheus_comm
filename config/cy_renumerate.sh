#!/bin/bash
pid=`pidof cyusb_linux`

#Call the standard cypress controller
if [ "$pid" ]; then
    kill -s SIGUSR1 $pid
fi


