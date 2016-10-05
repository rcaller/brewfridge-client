from relayControl import RelayControl
import logging
import sys

class Fridge:
  """temp controlled fridge"""
  def __init__(self, heatRelay, coolRelay, tempDelta):
    self.heatRelay = RelayControl(heatRelay)
    self.coolRelay = RelayControl(coolRelay)
    self.tempDelta = tempDelta
    self.coolRelay.setMinimumCycleTime(300)
    logger = logging.getLogger("DaemonLog")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    self.logger=logger


  def addLogger(self, logger):
    self.logger = logger
    self.heatRelay.addLogger(logger)
    self.coolRelay.addLogger(logger)

  def heat(self):
    self.log('heat')
    self.heatRelay.on()
    self.coolRelay.off()

  def cool(self):
    self.log('cool')
    self.coolRelay.on()
    self.heatRelay.off()

  def steady(self):
    self.log('steady')
    self.coolRelay.off()
    self.heatRelay.off()    

  def log(self, message):
    self.logger.warn(message)

  def control(self, target, current):
    self.log('control target: '+str(target)+'  current: '+str(current))
    tempDiff = target - current
    if (abs(tempDiff)<=self.tempDelta):
      self.steady()
    elif (tempDiff>0):
      self.heat()
    elif (tempDiff<0):
      self.cool()
