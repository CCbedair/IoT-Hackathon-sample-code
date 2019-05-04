from influxdb import InfluxDBClient
import cv2
import os
import numpy as np
import subprocess

def unique_count_app(a):
    colors, count = np.unique(a.reshape(-1,a.shape[-1]), axis=0, return_counts=True)
    return colors[count.argmax()]

THR_HUMIDITY = 20
THR_TEMP = 10
THR_LUMIN = 110

client_ruvi = InfluxDBClient('192.168.1.200', 8086, 'debian', 'debian', 'ruuvi1')
client_pi = InfluxDBClient('192.168.1.200', 8086, 'debian', 'debian', 'piroommonitor')


face_cascade = cv2.CascadeClassifier(
    os.path.join('haarcascade_frontalface_default.xml'))
person_cascade = cv2.CascadeClassifier(
    os.path.join('haarcascade_upperbody.xml'))
cap = cv2.VideoCapture("http://192.168.1.79:8081")
#cap = cv2.VideoCapture(0)

BLACK = np.zeros((640, 360, 3), np.uint8)
RED = np.zeros((640, 360, 3), np.uint8)
RED[:] = [255,0,0]
BLUE = np.zeros((640, 360, 3), np.uint8)
BLUE[:] = [0,0,255]
WHITE = np.zeros((640, 360, 3), np.uint8)
WHITE[:] = [255,255,255]

while True:
    print("Querying Database")
    #result = client_ruvi.query('select temperature, humidity,  from ruuvi_measurements order by time desc limit 1 ')
    result = client_pi.query('select luminosity, humidity, temperature from piroommonitor order by time desc limit 1 ')
    faces = []
    bodies = []
    print result
    current_temp = current_lumin = current_humidity = 0
    for res in result:
        for entry in res:
            print entry
            current_temp = entry['temperature']
            current_humidity = entry['humidity']
            current_lumin = entry['luminosity']
    r, frame = cap.read()
    print("Caputring Feed")
    if r:
        frame = cv2.resize(frame,(640,360)) # Downscale to improve frame rate
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) # Haar-cascade classifier needs a grayscale image
        bodies_scale = person_cascade.detectMultiScale(gray_frame)
        faces_scale = face_cascade.detectMultiScale(gray_frame)

        for (x, y, w, h) in faces_scale:
            faces.append(frame[y:y+h, x:x+w])
            cv2.rectangle(frame, (x,y), (x+w,y+h),(0,255,0),2)

        for (x, y, w, h) in bodies_scale:
            bodies.append(frame[y:y+h, x:x+w])
            cv2.imshow("bodies", bodies[-1])
            cv2.rectangle(frame, (x,y), (x+w,y+h),(255,255,0),2)
        cv2.imshow("feed", frame)
    #print len(bodies), len(faces), current_temp, current_lumin, current_humidity

        if len(bodies) < 1 and len(faces)< 1:
            cv2.imshow("preview", WHITE)
        else:
            if current_humidity >= THR_HUMIDITY and current_temp <= THR_TEMP:
                cv2.imshow("preview", BLUE)
            else:
                cv2.imshow("preview", RED)
    if current_lumin > THR_LUMIN:
        brightness = float(subprocess.check_output("brightness -l | tail -1 | awk 'NF{ print $NF }'", shell=True).strip())
        brightness = max(brightness- 0.1, 0.5)
        os.system('brightness ' + str(brightness))
    else:
        brightness = float(subprocess.check_output("brightness -l | tail -1 | awk 'NF{ print $NF }'", shell=True).strip())
        brightness = min(brightness + 0.1, 1)
        os.system('brightness ' + str(brightness))
    k = cv2.waitKey(1)
    if k & 0xFF == ord("q"): # Exit condition
        break
