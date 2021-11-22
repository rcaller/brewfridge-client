#!/usr/bin/python
from BaseHTTPServer import HTTPServer

from brewFridgeEventsRequestHandler import BrewFridgeEventsRequestHandler

PORT_NUMBER = 8080

try:
	#Create a web server and define the handler to manage the
	#incoming request
	server = HTTPServer(('', PORT_NUMBER), BrewFridgeEventsRequestHandler)
	print 'Started httpserver on port ' , PORT_NUMBER
	
	#Wait forever for incoming htto requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()
	
