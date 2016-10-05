import unittest
import os
from mock import patch, MagicMock
from relayControl import RelayControl 

wiringMock = MagicMock() 
timeMock = MagicMock()

class relayControlTest(unittest.TestCase):
  def test_construction(self):
    relay = RelayControl(6)
    self.assertEquals(relay.__class__.__name__, "RelayControl")

  @patch('relayControl.wiringpi', wiringMock)  
  def test_wiringpi_setup(self):
    relay = RelayControl(6)    
    assert wiringMock.wiringPiSetup.called

  @patch('relayControl.wiringpi', wiringMock)
  def test_on(self):
    relay = RelayControl(6)
    relay.on();
    wiringMock.digitalWrite.assert_called_with(6,1)

  def test_on_sets_ison(self):
    relay = RelayControl(6)
    relay.on();
    self.assertTrue(relay.isOn())

  @patch('relayControl.wiringpi', wiringMock)
  def test_off(self):
    relay = RelayControl(6)
    relay.on()
    relay.off()
    wiringMock.digitalWrite.assert_called_with(6,0)


  def test_off_sets_ison(self):
    relay = RelayControl(6)
    relay.on()
    relay.off()
    self.assertFalse(relay.isOn())

  def test_set_minimum_cycle_time(self):
    relay = RelayControl(6)
    relay.setMinimumCycleTime(5)
    self.assertEquals(relay.minCycleTime, 5)

  @patch('relayControl.wiringpi', wiringMock)
  def test_on_when_already_on_does_not_switch(self):
    wiringMock.digitalWrite.reset_mock()
    relay = RelayControl(6)
    relay.on()
    relay.on()
    wiringMock.digitalWrite.assert_called_once_with(6,1)

  @patch('relayControl.wiringpi', wiringMock)
  def test_off_when_already_off_does_not_switch(self):
    relay = RelayControl(6)
    relay.on()
    wiringMock.digitalWrite.reset_mock()
    relay.off()
    relay.off()
    wiringMock.digitalWrite.assert_called_once_with(6,0)

  def test_check_cycle_time_returns_true_if_over_cycle_time(self):
    relay = RelayControl(6)
    relay.setMinimumCycleTime(0)
    self.assertTrue(relay.checkCycleTime())

  def test_check_cycle_time_returns_false_if_over_cycle_time(self):
    relay = RelayControl(6)
    relay.setMinimumCycleTime(120)
    self.assertFalse(relay.checkCycleTime())

  @patch('relayControl.time', timeMock)
  def test_set_switch_time(self):
    relay = RelayControl(6)
    relay.setSwitchTime()
    timeMock.time.assert_called_with()

  
     

if __name__ == '__main__':
    unittest.main()
