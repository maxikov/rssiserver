#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import threading
import cgi
import re
import json
import MySQLdb
import urlparse
import datetime
import time
import wsgiref.handlers

def db_init():
	db = MySQLdb.connect(host = "localhost", user = "root",	passwd = "12345" , db = "rssi_mapper_user_locations")
	db.set_character_set('utf8')
	c = db.cursor()
	c.execute('SET NAMES utf8')
	c.execute('SET CHARACTER SET utf8')
	c.execute('SET character_set_connection=utf8')
	return db, c

class HTTPRequestHandler(BaseHTTPRequestHandler):
 
    def address_string(self): #Fix for the slow response
        host, _ = self.client_address[:2]
        return host
 
    def do_POST(self):
	if None != re.search('/user_locations.json', self.path):
		ctype, _ = cgi.parse_header(self.headers.getheader('content-type'))
		if "application/json" == ctype:
			length = int(self.headers.getheader('content-length'))
			data = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
			print data
			try:
				parsed_data = json.loads(data.keys()[0])
			except Exception as e:
				print e
				self.send_response(400, "Failed to parse json: " + str(e))
				return
			else:
				try:
					print "wat"
					timestamp = parsed_data["user_location"]["timestamp"]
					print timestamp
					ipaddr = parsed_data["user_location"]["ipaddr"]
					print ipaddr
					macaddr = parsed_data["user_location"]["mac"]
					print macaddr
					imei = parsed_data["user_location"]["imei"]
					print imei
					lac = parsed_data["user_location"]["lac"]
					print lac
					latitude = parsed_data["user_location"]["latitude"]
					print latitude
					longitude = parsed_data["user_location"]["longitude"]
					print longitude
					altitude = parsed_data["user_location"]["altitude"]
					print altitude
					RSSI = parsed_data["user_location"]["RSSI"]
					print RSSI
				except Exception as e:
					print e
					self.send_response(400, "Incorrect json: " + str(e))
					return
				else:
					try:
						db, c = db_init()
						query_template = "INSERT INTO rssi_mapper_user_locations (timestamp, ipaddr, macaddr, imei, lac, latitude, longitude, altitude, RSSI) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
						c.execute(query_template, (timestamp, ipaddr, macaddr, imei, lac, latitude, longitude, altitude, RSSI))
						c.close()
						db.commit()
						db.close()
					except Exception as e:
						print e
						self.send_response(500, str(e))
						return
					else:
						self.send_response(200, "OK")
						print timestamp, ipaddr, macaddr, imei, lac, latitude, longitude, altitude, RSSI
						return
	self.send_response(400, "Bad request")
        
    def do_GET(self):
	if None != re.search("/api/v1/user_locations/rssi", self.path):
		try:
			params = urlparse.parse_qs(urlparse.urlparse(self.path).query)
			start = int(params["start"][0])
			stop = int(params["stop"][0])
			limit = int(params["limit"][0])
		except Exception as e:
			print e
			self.send_response(400, "Bad url: " + str(e))
			self.wfile.close()
			return
		else:
			try:
				db, c = db_init()
				query_template = "SELECT timestamp, latitude, longitude, altitude, RSSI from rssi_mapper_user_locations WHERE timestamp >= %s AND timestamp <= %s LIMIT %s"
				c.execute(query_template, (start, stop, limit))
				res = c.fetchall()
				c.close()
				db.close()
			except Exception as e:
				print e
				self.send_response(500, "DB error: " + str(e))
				self.wfile.close()
				return
			else:
				self.send_response(200, "OK")
				#print res
				formatted_response = [{"timestamp": int(row[0]), "latitude": float(row[1]), "longitude": float(row[2]), "altitude": float(row[3]), "rssi": int(row[4])} for row in res]
				#print formatted_response
				json_response = json.dumps(formatted_response)
				print json_response
				self.send_header('Content-Type', "application/json")
				self.send_header('Content-Length', len(json_response))
				#print "len:", len(json_response)
				now = datetime.datetime.now()
				stamp = time.mktime(now.timetuple())
				timestamp = wsgiref.handlers.format_date_time(stamp)
				#print "timestamp:", timestamp
				self.send_header('Date', timestamp)
				self.end_headers()
				self.wfile.write(json_response)
				self.wfile.close()
				print "wat?"
				return
	self.send_response(400, "Bad request")
	self.wfile.close()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
 
    def shutdown(self):
        self.socket.close()
        HTTPServer.shutdown(self)
 
class SimpleHttpServer():
    def __init__(self, ip, port):
        self.server = ThreadedHTTPServer((ip,port), HTTPRequestHandler)
 
    def start(self):
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = False
        self.server_thread.start()
 
    def waitForThread(self):
        self.server_thread.join()
 
    def stop(self):
        self.server.shutdown()
        self.waitForThread()


def main():
    http_server = SimpleHttpServer('', 31415)
    print 'HTTP Server Running...........'
    http_server.start()
    http_server.waitForThread()
    
if __name__ == "__main__":
    main()
