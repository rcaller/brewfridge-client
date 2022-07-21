#!/usr/bin/python

import json

import time
import os
import glob
import sys
import threading
import logging
import logging.handlers
import targetTemp
import wiringpi
import sqlite3
import daemon
import configparser
from subprocess import check_output
from fridge import Fridge
from pid import Pid
import TiltHydrometer
import urllib
from http.server import HTTPServer
wiringpi.wiringPiSetup()
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_files = {};


def read_temp_raw(deviceFile):
    try:
      f = open(deviceFile, 'r')
      lines = f.readlines()
      f.close()
    except:
      logger.error("Probem accessing temperature sensor ")
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
        parser = configparser.ConfigParser()
        parser.read("brewConfig.txt")
        self.name =  parser.get("controller", "name")
        self.baseUrl = parser.get("controller", "baseUrl")
        self.apiKey = parser.get("controller", "apiKey")
        self.targetTemp = targetTemp.targetTemp(self.baseUrl, self.apiKey)
        self.target=20
        heatPin = int(parser.get("tempController", "heatPin"))
        heatDelay  = int(parser.get("tempController", "heatDelay"))
        coolPin = int(parser.get("tempController", "coolPin"))
        coolDelay =  int(parser.get("tempController", "coolDelay"))
        threshold =  float(parser.get("tempController", "threshold"))
        p = float(parser.get("pid", "proportional"))
        i =  float(parser.get("pid", "integral"))
        d =  float(parser.get("pid", "differential"))
        window = int(parser.get("pid", "window"))
        self.fridge = Fridge(heatPin,coolPin,threshold, heatDelay, coolDelay)
        self.fridge.addLogger(logger)
        self.pid = Pid(p, i, d, window)
        self.pid.addLogger(logger)
        for dev, id in parser.items("tempSensors"):
          logger.info(dev)
          device_files[dev] = (base_dir + id + "/w1_slave")
        logger.info("Setup complete")


    def update_target_temp(self):
       try:
         logger.info("Getting Target")
         target = self.targetTemp.getTargetTemp(self.fermentId, self.profileId)
         self.target = target
         logger.info("target: "+str(target))
       except BaseException as err:
         logger.error("Error getting temperature "+str(err))

    def init_ferment_details(self):
      req = urllib.request.Request(self.baseUrl+"fermenters?fermenterName="+self.name)
      req.add_header('x-api-key', self.apiKey)
      r = json.loads(urllib.request.urlopen(req).read())
      self.fermentId = r["Item"]["fermentId"]
      self.profileId = r["Item"]["profileId"]

    def report_data(self, data):
      req = urllib.request.Request(self.baseUrl+"fermentationReport?fermentId="+str(self.fermentId))
      req.add_header('Content-Type', 'application/json')
      req.add_header('x-api-key', self.apiKey)
      logger.info("Reporting Temps - ")
      try:
        reportData =  json.dumps({"fermentId": self.fermentId}|data)
        logger.info(reportData)
        response = urllib.request.urlopen(req, reportData.encode('utf-8'))
        logger.info(response)
      except BaseException as e:
        logger.error("Write failure: "+str(e))
 

    def run(self):
        logger.info("Getting fermentation id")
        self.init_ferment_details()

        logger.info("Start Main Loop")
        brewometer = TiltHydrometer.TiltHydrometerManager(False, 60, 40)
        brewometer.addLogger(logger)
        brewometer.start()
        while True:
          self.update_target_temp()
          data = {}
          brewometerData = brewometer.getValue('Pink')
          logger.info("Brewometer: "+str(brewometerData));
          brewometerTemp = None
          brewometerGravity = None
          if (brewometerData):
            data["tilt"] = brewometerData.temperature;
            data["gravity"] = brewometerData.gravity;
          logger.info("Reading temps")

          logger.info(device_files)
          for dev in device_files:
            data[dev] = read_temp(dev)
            logger.info(dev + ":" + str(data[dev]))
          
          pid_target = self.target + self.pid.control(data["beer"], self.target)
          data['target'] = pid_target
          self.report_data(data) 
          #if (pid_target < 1):
          #  pid_target = 1
          logger.info("PID target:" + str(pid_target))
          for loopCount in range(0,5):
            logger.info("loop")
            controlTemp = read_temp('control')
            self.fridge.control(pid_target,  controlTemp) 
            time.sleep(10)



logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.handlers.WatchedFileHandler("/var/log/brewfridge.log")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Starting Daelmon")
dc = daemon.DaemonContext()
dc.files_preserve=[handler.stream]
dc.working_directory=os.getcwd()
with dc:
  BrewFridge().run()
