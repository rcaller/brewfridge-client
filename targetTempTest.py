import unittest
import os

import targetTemp  

class targetTempTests(unittest.TestCase):
  def test_construction(self):
    target = targetTemp.targetTemp("test");
    self.assertEquals(target.__class__.__name__, "targetTemp")

  def test_source_set(self):
    target = targetTemp.targetTemp("test");
    self.assertEquals(target.sourceURL, "test");

  def test_get_target_data(self):
    testDataPath = os.path.dirname(os.path.abspath(__file__)) + "/testdata/1"
    target = targetTemp.targetTemp("file://"+testDataPath)
    self.assertEquals(target.getTargetTemp(), 1) 


if __name__ == '__main__':
    unittest.main()
