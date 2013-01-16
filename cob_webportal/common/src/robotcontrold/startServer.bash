#!/bin/bash
if screen -ls | grep robotcontrold > /dev/null; then
    echo 'Robotcontrold screen exists. Server still running?'
    echo 'If not kill the screen "robotcontrold"'
    exit
fi
screen -S robotcontrold -d -m sudo "$(dirname $0)/robotcontrold" --trac=/usr/local/trac/webportal2 --webPort=81 --timeout=3600 --logLevel=debug --console  --log=log.txt --sqliteDb=videodemo.sqlite
