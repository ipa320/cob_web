#!/bin/bash
echo "Stopping Server"
sudo su www-data -c "screen -S robotcontrold -X quit"
exit $?
