import logging
from collections import deque
import sys

class Pid:
  def __init__(self, p, i, d, window):
    self.p = p
    self.i = i
    self.d = d
    self.window = window  
    self.deque = deque([], window)
    self.prev=0
    logger = logging.getLogger("DaemonLog")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    self.logger=logger

  def addLogger(self, logger):
    self.logger = logger

  def control(self, current, target):
    proportional = self.p * (target - current)
    differential = self.d * self.differential(current, target)
    integral = self.i * self.integral(current, target)
    self.logger.info("P: " + str(proportional))
    self.logger.info("I: " + str(integral))
    self.logger.info("D: " + str(differential))
    control_value = proportional + differential + integral
    return round(control_value, 2)

  def integral(self, current, target):
    if (self.window == 0):
      return 0
    self.deque.append(target-current) 
    return sum(self.deque)/self.window

  def differential(self, current, target):
    if self.prev==0:
      self.prev = current
      return 0
    diff = current-self.prev
    self.prev = current
    return diff
