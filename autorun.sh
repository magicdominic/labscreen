#!/bin/bash
cd /home/pi/labscreen
while [[ True ]]; do
    #statements
    export DISPLAY=:0
    python3 main.py
done
