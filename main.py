#!/bin/env python3
import threading
import curses
import signal
import traceback
import os
import pygame

file = '/home/pi/labscreen/sheep-human.wav'
pygame.init()
pygame.mixer.init()
pygame.mixer.music.load(file)
pygame.mixer.music.play(loops=-1)

from showpic import *

pilImage = Image.open("zeitung.png")
showPIL(pilImage)



