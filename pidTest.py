import unittest

from pid import Pid

class pidTest(unittest.TestCase):
  def test_construction(self):
    pid = Pid(1,1,1,100)
    self.assertEquals(pid.__class__.__name__, "Pid")

  def test_proportional(self):
    pid = Pid(1,0,0,0)
    self.assertEquals(pid.control(10, 20), 10)

  def test_integral_with_one_value(self):
    pid = Pid(0,1,0,5)
    self.assertEquals(pid.control(5,10), 5)

  def test_integhral_with_partially_full_window(self):
    pid = Pid(0,1,0,6)
    pid.control(5, 10)
    pid.control(6, 10)
    self.assertEquals(pid.control(7,10), 4)

  def test_integral_with_full_window(self):
    pid = Pid(0,1,0,5)
    pid.control(5,10)
    pid.control(5,10)
    pid.control(5,10)
    pid.control(5,10)
    self.assertEquals(pid.control(5,10), 5)

  def test_integral_with_over_flowed_window(self):
    pid = Pid(0,1,0,5)
    pid.control(5,10)
    pid.control(5,10)
    pid.control(5,10)
    pid.control(5,10)
    pid.control(5,10)
    pid.control(5,10)
    self.assertEquals(pid.control(5,10), 5)

  def test_differential(self):
     pid = Pid(0,0,1,0)
     pid.control(2,10)
     self.assertEquals(pid.control(5,10), 3)

  def test_differential_with_no_previous_value(self):
    pid = Pid(0,0,1,0)
    self.assertEquals(pid.control(5,10), 0)

if __name__ == '__main__':
    unittest.main()

