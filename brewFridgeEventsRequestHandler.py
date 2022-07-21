#!/usr/bin/python
from http.server import BaseHTTPRequestHandler
from feedgen.feed import FeedGenerator
import sqlite3
import json
import datetime
from pytz import timezone


PAGESIZE = 500

#This class will handles any incoming request from
#the browser 
class BrewFridgeEventsRequestHandler(BaseHTTPRequestHandler):

  def __db_connect(self):
    conn = sqlite3.connect('brewFridge.measurement_events', detect_types = sqlite3.PARSE_DECLTYPES)	
    conn.row_factory = sqlite3.Row
    return conn

  #Handler for the GET requests
  def do_GET(self):
    self.send_response(200)
    self.send_header('Content-type','application/xml')
    self.end_headers()
    if (self.path[1:] == 'head'):
      atom = self.createFeedHead()
    else:
      atom = self.createFeedPage(self.path[1:])
    self.wfile.write(atom)
    return

  def createAtomPage(self, events, prev):
    fg = FeedGenerator()
    fg.title('Events Feed')
    fg.id('id')
    if (prev != ""):
      fg.link(href=prev, rel='prev')
    for event in events:
      fe = fg.add_entry()
      fe.id(str(event['id']))
      fe.title("MeasurementEvent")
      fe.content(content = event['data'])
      fe.published(event['time'])
    return fg.atom_str(pretty=True)

  def createFeedHead(self):
    prev = '/'+str(self.getPageCount())
    events = self.getHeadEvents()
    return self.createAtomPage(events, prev)

  def createFeedPage(self, pageNum):
    events = self.getEventsPage(pageNum)
    prev = ""
    if (int(pageNum)>0):
      prev='/'+str(int(pageNum)-1)
    return self.createAtomPage(events, prev)


  def getHeadEvents(self):
    headSize = self.getHeadSize()
    conn = self.__db_connect();
    c = conn.cursor()
    c.execute("SELECT * from tempMeasurementTaken ORDER BY time DESC LIMIT "+str(headSize))
    rawEvents = c.fetchall()
    conn.close();
    return self.createEventsFromRaw(rawEvents)

  def getEventsPage(self, pageNum):
    headSize = self.getHeadSize()
    offset = int(pageNum)*PAGESIZE
    conn = self.__db_connect();
    c = conn.cursor()
    sql = "SELECT * from tempMeasurementTaken LIMIT "+str(PAGESIZE)+" OFFSET "+str(offset)
    c.execute(sql)
    rawEvents = c.fetchall()
    conn.close();
    return self.createEventsFromRaw(rawEvents)

  def createEventsFromRaw(self, rawEvents):
    events = []
    for rawEvent in rawEvents:
      localTime = timezone('Europe/London').localize(rawEvent['time'])
      event = dict(id=rawEvent['tempMeasurementId'], time = localTime, data = json.dumps(dict(rawEvent)), contentType = 'application/json')
      events.append(event)
    return events

  def getPageCount(self):
    conn = self.__db_connect();
    c = conn.cursor()
    c.execute("SELECT count(*) from tempMeasurementTaken")
    return (c.fetchone()[0]//PAGESIZE)-1

  def getHeadSize(self):
    conn = self.__db_connect();
    c = conn.cursor()
    c.execute("SELECT count(*) from tempMeasurementTaken")
    return c.fetchone()[0]%PAGESIZE
