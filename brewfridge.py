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
from daemon import runner
from subprocess import check_output
from fridge import Fridge
from pid import Pid
import Brewometer

wiringpi.wiringPiSetup()
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_files = {'4bfe': '/sys/bus/w1/devices/28-000006c54bfe/w1_slave',
                '6df9': '/sys/bus/w1/devices/28-000006c56df9/w1_slave'};


def read_temp_raw(deviceFile):
    f = open(deviceFile, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(device):
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
        self.targetTemp = targetTemp.targetTemp("http://www.lrp-world.org/brewfridge/tempdata/target")
        self.target=20
        self.fridge = Fridge(8,9, 0.25)
        self.fridge.addLogger(logger)
        self.pid = Pid(2,6,-1,60)
        self.pid.addLogger(logger)

    def run(self):
        logger.info("Start Main Loop")
        brewometer = Brewometer.BrewometerManager(False, 60, 40)
        brewometer.addLogger(logger)
        brewometer.start()
        logger.info(os.getcwd())
        while True:

          try:
            logger.info("Getting Target")
            target = self.targetTemp.getTargetTemp()
          except:
            logger.error("Error getting temperature")
          logger.info(target)
          self.target = target
          brewometerData = brewometer.getValue('Red')
          
          logger.info("Brewometer: "+str(brewometerData));
          brewometerTemp = None
          brewometerGravity = None
          if (brewometerData):
	    brewometerTemp = brewometerData.temperature;
            brewometerGravity = brewometerData.gravity;
          temp_6df9 = read_temp('6df9')
          logger.info("Beer:" + str(temp_6df9))
          pid_target = self.target + self.pid.control(temp_6df9, self.target)
          if (pid_target < 1):
            pid_target = 1
          logger.info("PID target:" + str(pid_target))
          for loopCount in range(0,5):
            logger.info("loop")
            temp_4bfe = read_temp('4bfe')
            self.fridge.control(pid_target,  temp_4bfe) 
            time.sleep(10)

          req = urllib2.Request('http://www.lrp-world.org:3000/tempreport')
          req.add_header('Content-Type', 'application/json')
          logger.info("Reporting Temps")
          try:
            response = urllib2.urlopen(req, json.dumps({'fridge': temp_4bfe, 'beer': temp_6df9, 'internal': brewometerTemp, 'gravity': brewometerGravity}))
          except:
            logger.error("Write failure")
        logger.info("loop2")



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
daemon.do_action()
