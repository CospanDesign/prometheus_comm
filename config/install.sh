#!/bin/bash

CURDIR=`pwd`

A=`whoami`

if [ $A != 'root' ]; then
   echo "You have to be root to run this script"
   exit 1;
fi


echo "Replacing Cypress's cy_renumerate.sh with this one"
cp $CURDIR/cy_renumerate.sh /usr/bin
chmod 777 /usr/bin/cy_renumerate.sh

