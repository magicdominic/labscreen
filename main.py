#!/bin/env python3
import threading
import curses
import signal
import traceback
import os
import pygame
import time

time.sleep(5)	

file = '/home/pi/labscreen/Labor_acht_drei_eins.wav'
pygame.init()
pygame.mixer.init()
pygame.mixer.music.load(file)
pygame.mixer.music.play(loops=-1)

from showpic import *

pilImage = Image.open("Gefaessnamen_bildschirm.png")
showPIL(pilImage)



