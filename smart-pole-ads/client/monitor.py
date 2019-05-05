from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import subprocess
import cgi
from threading import Thread

PORT_NUMBER = 8080

#This class will handles any incoming request from
#the browser
p = subprocess.Popen(["open", "ad.jpeg"])
class myHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    def do_POST(self):
        global p
        try:
            self._set_headers()
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            # print form.getvalue('file')
            filename = "ad.jpeg"
            file_length = int(self.headers['Content-Length'])
            with open(filename, 'wb') as output_file:
                output_file.write(form.getvalue('file'))
                output_file.close()

            # rf = open(filename, 'rb')
            # print rf.read()
            p.kill()
            p = subprocess.Popen(["open", "ad.jpeg"])
                # self.send_response(200)
        except Exception as e:
            print e
            self.send_response(301)

try:
	#Create a web server and define the handler to manage the
	#incoming requestad_displayer = AdDisplay()
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	print 'Started httpserver on port ' , PORT_NUMBER
	#Wait forever for incoming htto requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()
