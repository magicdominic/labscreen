#!/bin/env python3
import threading
import curses
import signal
import traceback
import os
import time
##### von app kopiert
import curses
import json
import logging
import os
import selectors
import serial
import subprocess
import sys
import time
import threading
######
import pygame

file = '/home/pi/labscreen/sheep-human.wav'
pygame.init()
pygame.mixer.init()
pygame.mixer.music.load(file)
pygame.mixer.music.play(loops=-1)

from showpic import *

pilImage = Image.open("zeitung.png")
showPIL(pilImage)





'''from helpers import *
from crossword import Crossword
from progress_bar import ProgressBar
from door_panel import DoorPanel
from management_interface import ManagementInterface
from widget_manager import WidgetManager
from shooting_range import ShootingRange, ShootingRangeState
from waitable_timer import WaitableTimer
from final_screen import FinalScreen'''



class Application:
    def __init__(self, screen):
        self.sel = selectors.DefaultSelector()
        self.screen = screen

        self.is_running = False
        self.with_cheats = '--with-cheats' in sys.argv

        #curses.raw() # disable special keys and stuff (such as ctrl-c)
        self.screen.nodelay(True) # disable blocking on getch()
        curses.curs_set(False) # hide cursor
        curses.mousemask(curses.ALL_MOUSE_EVENTS) # enable mouse interaction
        curses.nonl() # don't translate KEY_RETURN into '\r\n'

        self.screen.clear()

        # create server for remote control
        self.mi = ManagementInterface(1234, self.sel)
        log.info("local address: {}".format(self.mi.get_local_addresses()))

        self.mi.register_handler('sound', self.sound)
        self.mi.register_handler('image', self.image)))
       

        

        # center in middle of screen (also take progress bar into account)
        ps = self.puzzle.size()
        try:
            self.puzzle.move(Vector(
                    int((w-ps.x)/2),
                    int((h-ps.y+6)/2)
            ))
        except Exception as e:
            raise Exception("Failed to move curses window. This can happen if your screen is too small!\nMaybe you forgot to switch to fullscreen?")

        self.progress_bar = ProgressBar(
                self,
                self.puzzle.pos() - Vector(0,5),
                Vector(self.puzzle.size().x, 5),
                'Lösungsfortschritt:')
        self.puzzle.progress_bar = self.progress_bar
        self.puzzle.solved_callback = self.on_crossword_solved

        self.door_panel = DoorPanel(self)
        self.door_panel.center_in(self.screen)
        self.widget_mgr.add(self.door_panel)
        self.door_panel.visible = False
        #self.widget_mgr.focus = self.door_panel

        self.shooting_range = ShootingRange(self)
        self.widget_mgr.add(self.shooting_range)
        self.shooting_range.first_shot_callback = self.show_shooting_range
        self.shooting_range.closed_callback = self.on_shooting_range_closed
        self.shooting_range.visible = False
        #self.widget_mgr.focus = self.shooting_range

        if self.shooting_range.target is None:
            self.widget_mgr.show_popup("Schwerwiegender Fehler", "Konnte keine Verbindung zum Reddot-Target aufbauen. "
                    "Schiessstand ist deaktiviert, keine Bonuszeit erschiessbar. "
                    "Dies sollte nicht passieren, bitte melden Sie diesen Fehler der Spielleitung.")
        else:
            self.sel.register(self.shooting_range.target.shots_queue_available, selectors.EVENT_READ, self.handle_shot)
            self.sel.register(self.shooting_range.target.has_raised_exception, selectors.EVENT_READ, self.handle_exception_in_reddot_target)

        self.final_screen = FinalScreen(self)
        self.final_screen.visible = False
        self.widget_mgr.add(self.final_screen)

    def __del__(self):
        self.exit()

    def set_timeout(self, seconds):
        self.TIMEOUT = seconds
        self.time_ends = time.time() + self.TIMEOUT
        self.timeout_timer.reset(self.TIMEOUT) # stop any running timer (if any) and set new timeout
        self.timeout_timer.start()

    def on_timeout(self):
        log.info("main application timeout!")
        self.mi.send_packet({
            'event': 'main_timeout',
        })

        self.puzzle.visible = False
        self.shooting_range.visible = False
        self.door_panel.visible = False
        self.final_screen.visible = True
        self.widget_mgr.focus = self.final_screen
        self.screen.clear()
        self.screen.refresh()
        self.widget_mgr.show_popup("Zeit Abgelaufen", "Ihre Zeit ist leider rum. Bitte begeben Sie sich zum Ausgang.\nFreundlichst, Ihre Spielleitung")
        self.widget_mgr.render()

    def handle_input(self, stdin):
        k = self.screen.get_wch()
        if k == curses.KEY_F1:
            self.show_help()
        elif k == curses.KEY_F12:
            self.show_about()
        elif k == curses.KEY_F9:
            if self.with_cheats:
                self.show_admin_screen()
            else:
                self.widget_mgr.show_input("Management Terminal", "Bitte Passwort eingeben:", self.show_admin_screen, True)
        else:
            if not self.widget_mgr.handle_input(k):
                log.info("unhandled key '{}'".format(k))

    def handle_shot(self, _):
        self.shooting_range.target.shots_queue_available.clear()
        while not self.shooting_range.target.shots_queue.empty():
            self.shooting_range.handle_shot(self.shooting_range.target.shots_queue.get())

    def show_about(self):
        self.widget_mgr.show_single_popup('Kreuzworträtsel',
                """Geschrieben von Samuel Bryner
Diese Software ist frei verfügbar unter der GPL. Quellcode unter
https://github.com/iliis/crossword
""")

    def show_admin_screen(self, pw=None):
        if pw == "ehrichweiss" or self.with_cheats:
            ser_port = "not connected"
            if self.shooting_range.target is not None:
                ser_port = self.shooting_range.target.ser.name

            self.widget_mgr.show_single_popup('Admin',
                    'Serial Port: {}\n\n'.format(ser_port)
                    +'Local Address:\n{}\n'.format('\n'.join(' - {}'.format(a) for a in self.mi.get_local_addresses()))
                    +'Local Port: {}\n'.format(self.mi.port)
                    +'Remote Control Connections:\n{}\n'.format('\n'.join(' - {}'.format(c.getpeername()) for c in self.mi.connections)),
                    callback=self._admin_screen_cb,
                    buttons=['CLOSE', 'AUTOFILL', 'SHOW SRANGE', 'RESET ALL', 'EXIT APP'])
        else:
            self.widget_mgr.show_single_popup('Passwort Falsch', 'Die Management Konsole ist nur für die Spielleitung gedacht, sorry.')

    def _admin_screen_cb(self, button):
        if button == 'EXIT APP':
            log.info("Exiting application through admin panel.")
            self.exit()
        elif button == 'RESET ALL':
            self.reset()
        elif button == 'AUTOFILL':
            self.puzzle.autofill()
        elif button == 'SHOW SRANGE':
            self.show_shooting_range()

    def exit_app_by_packet(self, packet):
        log.info("Exiting application trough remote command.")
        self.exit()

    def exit(self):
        self.is_running = False
        # if something fails, shooting_range is not yet created, thus we
        # trigger another exception when trying to set this variable. To
        # protect against this, let's check if the member variable exists
        # before accessing it
        if hasattr(self, 'shooting_range') and self.shooting_range.target is not None:
            self.shooting_range.target.is_running = False

    def show_popup_from_packet(self, packet):
        if not 'title' in packet or not 'text' in packet:
            raise ValueError("Invalid command: missing 'title' or 'text' field.")

        if 'buttons' in packet:
            buttons = packet['buttons']
        else:
            buttons = ['OK']

        self.widget_mgr.show_single_popup(
                packet['title'],
                packet['text'],
                buttons=buttons)

    def on_crossword_solved(self, _):
        self.puzzle.visible = False
        self.door_panel.visible = True
        self.widget_mgr.focus = self.door_panel

    def show_shooting_range(self):
        if not self.shooting_range.visible:
            if self.shooting_range.state == ShootingRangeState.NOT_WORKING:
                raise Exception("Cannot start shooting range: Target is not working.")
            else:
                self.shooting_range.visible = True
                self.focus_last = self.widget_mgr.focus
                self.widget_mgr.focus = self.shooting_range

    def on_shooting_range_closed(self, _):
        self.shooting_range.visible = False
        self.widget_mgr.focus = self.focus_last
        self.time_ends += self.shooting_range.points_to_bonus_time()
        self.timeout_timer.reset(self.remaining_time_in_seconds()) # stop any running timer (if any) and set new timeout
        self.timeout_timer.start()

    def handle_exception_in_reddot_target(self, _):
        self.shooting_range.target.has_raised_exception.clear()
        exc, info = self.shooting_range.target.cached_exception
        raise exc from None

    def remaining_time_in_seconds(self):
        return max(math.ceil(self.time_ends - time.time()), 0)

    def remaining_time(self):
        return time_format(self.remaining_time_in_seconds())

    def shutdown(self, packet):
        log.info("Shutting down PC!!")
        subprocess.call(["sudo", "halt"])
    
    def show_help(self):
        # TODO: write help screen
        self.widget_mgr.show_single_popup('Hilfe',
                'Für jeden Verbrecher gibt es ein Rätsel. Löse die Rätsel und trage die Lösungsworte hier im Kreuzworträtsel ein um auszubrechen. Pfeiltasten auf der Tastatur benutzen zum navigieren. Sobald alles korrekt ausgefüllt ist erscheint die Türsteuerung. Bei Fragen oder wenn Ihr einen Tipp braucht einfach mit dem Telefon anrufen: kurbeln und Höhrer ans Ohr halten.')

    def reset(self):
        log.info("Resetting application!")
        self.screen.clear()
        self.puzzle.reset()

        self.door_panel.reset()
        self.door_panel.visible = False
        self.shooting_range.visible = False
        self.shooting_range.reset()
        self.puzzle.visible = True
        self.final_screen.visible = False
        self.set_timeout(self.TIMEOUT)

        self.widget_mgr.focus = self.puzzle

    def run(self):
        #ser.write(b'crossword running')
        self.is_running = True

        while self.is_running:
            self.widget_mgr.render()
            events = self.sel.select()

            for key, mask in events:
                callback = key.data
                callback(key.fileobj)





































"""from app import Application, log

# ignore CTRL+V keybinding
#signal.signal(signal.SIGINT, signal.SIG_IGN)

def main(screen):
    try:
        app = Application(screen)
        app.run()
        return None, None
    except Exception as e:
        log.error("Unhandled Exception: {}".format(e))
        log.error(traceback.format_exc())
        return e, traceback.format_exc()



if __name__ == '__main__':
    log.info("starting application")
    ex, bt = curses.wrapper(main)

    if ex is not None:
        # try to display exception on screen

        curses.endwin() # this doesn't really work somehow :(
        # and manually sending ANSI escape codes is not enough :(
        os.system("clear")
        os.system("reset")
        os.system("stty sane")
        os.system("tput rs1")

        print("\033[4m\033[1mUnhandled Exception\033[0m") # bold, underlined
        print("\033[31m\033[1m") # red, bold
        print(ex)

        print("\033[0m") # reset
        print("Backtrace:")
        print(bt)

        log.info("exiting after exception")

        #for t in threading.enumerate():
            #print("thread", t.name, ": ", t, "daemon?", t.daemon)
        sys.exit(-1)
    else:
        log.info("exited cleanly")
        sys.exit(0)"""
