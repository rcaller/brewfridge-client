from urllib.request import Request, urlopen
class targetTemp:
  """target temperature for current brew"""
  def __init__(self, sourceUrl, apiKey):
    self.sourceURL = sourceUrl + "fermentationTarget?fermentId="
    self.apiKey = apiKey

  def getTargetTemp(self, fermentId, profileId):
    req = Request(self.sourceURL+str(fermentId)+"&profileId="+str(profileId))
    req.add_header('x-api-key', self.apiKey)
    r = urlopen(req)
    return round(float(r.read()), 2) 
    
