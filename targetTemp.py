import urllib2
class targetTemp:
  """target temperature for current brew"""
  def __init__(self, sourceUrl):
    self.sourceURL = sourceUrl

  def getTargetTemp(self):
    try:
      r = urllib2.urlopen(self.sourceURL)
    except URLError as e:
      raise
    return round(float(r.read()), 2) 
    
