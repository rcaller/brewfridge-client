import unittest
import os
from mock import patch, MagicMock
from fridge import Fridge

heatMock = MagicMock() 
coolMock = MagicMock()
class fridgeTest(unittest.TestCase):
  def setUp(self):
    self.fridge = Fridge(5,6, 0.5)
    self.fridge.heatRelay = heatMock
    self.fridge.coolRelay = coolMock

  def test_construction(self):
    self.assertEquals(self.fridge.__class__.__name__, "Fridge")

  def test_heat(self):
    self.fridge.heat()    
    heatMock.on.assert_called()
    coolMock.off.assert_called()

  def test_cool(self):
    self.fridge.cool()
    coolMock.on.assert_called_with()
    heatMock.off.assert_called_with()

  def test_steady(self):
    self.fridge.steady()
    coolMock.off.assert_called_with()
    heatMock.off.assert_called_with()

  @patch('fridge.Fridge.steady')
  def test_control_at_target_temp(self, m):
    self.fridge.control(20,20)
    m.assert_called_with()

  @patch('fridge.Fridge.heat')
  def test_control_below_target_temp(self, m):
    self.fridge.control(20,18)
    m.assert_called_with()

  @patch('fridge.Fridge.cool')
  def test_control_below_target_temp(self, m):
    self.fridge.control(15,18)
    m.assert_called_with()


if __name__ == '__main__':
    unittest.main()
