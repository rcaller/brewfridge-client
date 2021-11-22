#!/usr/bin/python

import json
import urllib2
import time
import os
import glob
import sys
import thread
import threading
import logging
import logging.handlers
import targetTemp
import wiringpi
import sqlite3
from daemon import runner
from subprocess import check_output
from fridge import Fridge
from pid import Pid
import Brewometer
from BaseHTTPServer import HTTPServer
from brewFridgeEventsRequestHandler import BrewFridgeEventsRequestHandler

wiringpi.wiringPiSetup()
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_files = {'4bfe': '/sys/bus/w1/devices/28-000006c54bfe/w1_slave',
                '6df9': '/sys/bus/w1/devices/28-000006c56df9/w1_slave',
                'thermowell': '/sys/bus/w1/devices/28-041659025bff/w1_slave'};


def read_temp_raw(deviceFile):
    try:
      f = open(deviceFile, 'r')
      lines = f.readlines()
      f.close()
    except:
      logger.error("Probem accessing temperature sensor")
    return lines

def read_temp(device):
    logger.info("reading "+device)
    lines = read_temp_raw(device_files[device])
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c


class BrewFridge():
    def __init__(self):
        logger.info("init")
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path =  '/tmp/foo.pid'
        self.pidfile_timeout = 5
        self.targetTemp = targetTemp.targetTemp("http://www.tertiarybrewery.co.uk/brewfridge/tempdata/target")
        self.target=20
        self.fridge = Fridge(8,9, 0.25)
        self.fridge.addLogger(logger)
        self.pid = Pid(2,6,-1,60)
        self.pid.addLogger(logger)
        logger.info("Setup complete")

    def __db_connect(self):
      return sqlite3.connect('brewFridge.measurement_events')

    def event_store_setup(self):
      logger.info("Creating table")
      conn = self.__db_connect()
      c = conn.cursor()
      c.execute('''PRAGMA journal_mode = OFF''')
      c.execute('CREATE TABLE IF NOT EXISTS tempMeasurementTaken (tempMeasurementId INTEGER PRIMARY KEY, fridgeTemp float, beerTemp float, internalTemp float, gravity float, time timestamp);')
      conn.commit()
      conn.close()

    def update_target_temp(self):
       try:
         logger.info("Getting Target")
         target = self.targetTemp.getTargetTemp()
         self.target = target
         logger.info("target: "+str(target))
       except:
         logger.error("Error getting temperature")

    def publish_measurement_event(self, fridge, beer, internal, gravity):
      logger.info("Publishing event")
      try:
        conn = self.__db_connect()
        c = conn.cursor()
        c.execute('INSERT INTO tempMeasurementTaken (fridgeTemp, beerTemp, internalTemp, gravity, time) VALUES (?, ?, ?, ?, datetime("now"))', (fridge, beer, internal, gravity))
        conn.commit()
        conn.close()
      except:
        logger.error("Unexpected error:")
        logger.error(sys.exc_info()[0])
        logger.error(sys.exc_info()[1])
        logger.error(sys.exc_info()[2])
 

    def run(self):
        logger.info("Start Main Loop")
        self.event_store_setup()
        brewometer = Brewometer.BrewometerManager(False, 60, 40)
        brewometer.addLogger(logger)
        brewometer.start()
        try: 
          t = threading.Thread(target=self.eventServer)
          #t.daemon=True
          t.start()
        except:
          logger.error("Unexpected error:", sys.exc_info()[0])
        while True:
	  self.update_target_temp()

          brewometerData = brewometer.getValue('Yellow')
          logger.info("Brewometer: "+str(brewometerData));
          brewometerTemp = None
          brewometerGravity = None
          if (brewometerData):
	    brewometerTemp = brewometerData.temperature;
            brewometerGravity = brewometerData.gravity;
          logger.info("Reading temps")
          temp_6df9 = read_temp('6df9')
          logger.info("Beer:" + str(temp_6df9))
          temp_thermowell = read_temp('thermowell')
          logger.info("TW:" + str(temp_thermowell))
          pid_target = self.target + self.pid.control(temp_6df9, self.target)
          if (pid_target < 1):
            pid_target = 1
          logger.info("PID target:" + str(pid_target))
          for loopCount in range(0,5):
            logger.info("loop")
            temp_4bfe = read_temp('4bfe')
            self.fridge.control(pid_target,  temp_4bfe) 
            time.sleep(10)

          req = urllib2.Request('http://www.tertiarybrewery.co.uk/brewfridge/tempreport')
          req.add_header('Content-Type', 'application/json')
          logger.info("Reporting Temps")
          try:
            response = urllib2.urlopen(req, json.dumps({'fridge': temp_4bfe, 'beer': temp_6df9, 'internal': brewometerTemp, 'thermowell': temp_thermowell, 'gravity': brewometerGravity}))
          except:
            logger.error("Write failure")

	  self.publish_measurement_event(temp_4bfe, temp_6df9, brewometerTemp, brewometerGravity)
        logger.info("loop2")

    def eventServer(self):
      server = HTTPServer(('', 8080), BrewFridgeEventsRequestHandler)
      #Wait forever for incoming htto requests
      server.serve_forever()

logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.handlers.WatchedFileHandler("/var/log/brewfridge.log")
handler.setFormatter(formatter)
logger.addHandler(handler)


brewFridge = BrewFridge()
daemon= runner.DaemonRunner(brewFridge)
#This ensures that the logger file handle does not get closed during daemonization
daemon.daemon_context.files_preserve=[handler.stream]
daemon.daemon_context.working_directory=os.getcwd()
logger.info("Starting Daelmon")
daemon.do_action()
