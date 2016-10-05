import wiringpi 
import time
import logging
import sys


class RelayControl:
  """relay controller"""
  def __init__(self, relay):
    self.relay = relay
    self.minCycleTime=0
    self.turnedOn = False
    self.lastSwitchTime=time.time()
    wiringpi.pinMode(self.relay, 1)
    wiringpi.digitalWrite(self.relay, 1)

    logger = logging.getLogger("DaemonLog")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    self.logger=logger

  def addLogger(self, logger):
    self.logger = logger

  def on(self):
    if (not(self.turnedOn)):
      if (self.checkCycleTime()):
        wiringpi.pinMode(self.relay, 1)
        wiringpi.digitalWrite(self.relay, 0)
        self.turnedOn = True
        self.setSwitchTime()
      else:
        self.logger.info('Cycle time-locked off')
    

  def off(self):
    if (self.turnedOn):
      wiringpi.pinMode(self.relay, 1)
      wiringpi.digitalWrite(self.relay, 1)
      self.turnedOn = False
      self.setSwitchTime()



  def isOn(self):
    return self.turnedOn

  def setMinimumCycleTime(self, cycleTime):
    self.minCycleTime=cycleTime
    self.logger.info('Min Cycle Time Set To - '+str(self.minCycleTime))

  def checkCycleTime(self):
    return (time.time() - self.lastSwitchTime) > self.minCycleTime

  def setSwitchTime(self):
    self.lastSwitchTime = time.time()
