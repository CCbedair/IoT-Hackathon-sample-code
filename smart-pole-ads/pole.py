from threading import Thread
import cv2
from influxdb import InfluxDBClient
from time import time
import os
import numpy as np
import subprocess
import requests


def unique_count_app(a):
    colors, count = np.unique(a.reshape(-1,a.shape[-1]), axis=0, return_counts=True)
    return colors[count.argmax()]

class VideoGet:
    """
    Class that continuously gets frames from a VideoCapture object
    with a dedicated thread.
    """
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
    def start(self):
        Thread(target=self.get, args=()).start()
        return self

    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()
    def stop(self):
        self.stopped = True

class SensorGet:
    def __init__(self, username="debian", password="debian", port=8086, src='192.168.1.200'):
        self.client_pi = InfluxDBClient(src, port, username, password, 'piroommonitor')
        self.client_ruuvi = InfluxDBClient(src, port, username, password, 'ruuvi1')
        self.client_lights = InfluxDBClient(src, port, "nokia", "nokia", 'light')
        self.lumin = self.humidity = self.temperature = 0

    def get(self):
        result = self.client_ruuvi.query('select humidity, temperature, mac from ruuvi_measurements order by time desc limit 10 ')
        for res in result:
            for entry in res:
                if entry['mac'] == "C32C696E2492":
                    self.temperature = entry['temperature']
                    self.humidity = entry['humidity']
                    break
        result = self.client_lights.query('select Lux from light order by time desc limit 1 ')
        for res in result:
            for entry in res:
                self.lumin = entry['Lux']
        #self.lumin = entry['luminosity']

class FrameProcessor:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(os.path.join('haarcascade_frontalface_default.xml'))
        self.person_cascade = cv2.CascadeClassifier(os.path.join('haarcascade_upperbody.xml'))

    def getBodies(self, frame):
        bodies = []
        frame = cv2.resize(frame,(640,360)) # Downscale to improve frame rate
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) # Haar-cascade classifier needs a grayscale image
        bodies_scale = self.person_cascade.detectMultiScale(gray_frame)
        for (x, y, w, h) in bodies_scale:
            bodies.append(frame[y:y+h, x:x+w])
            #cv2.imshow("bodies", bodies[-1])
        return bodies

    def getFaces(self, frame):
        faces = []
        frame = cv2.resize(frame,(640,360)) # Downscale to improve frame rate
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) # Haar-cascade classifier needs a grayscale image
        faces_scale = self.face_cascade.detectMultiScale(gray_frame)
        for (x, y, w, h) in faces_scale:
            faces.append(frame[y:y+h, x:x+w])
            cv2.imshow("faces", faces[-1])
        return faces

class AdGet:
    def __init__(self):
        self.dim = False
        self.THR_HUMIDITY = 20
        self.THR_TEMP = 26
        self.THR_LUMIN = 10
        self.ttd = int(time()) + 10
        self.ad = "aalto.jpeg"
        self.dest = ['192.168.1.56']#, '192.168.1.150']

    def get(self, params, faces, bodies):
        #print self.ttd, int(time())
        self.dim = False
        lumin, temp, humid = params

        # #Debug for lumin
        # if int(time()) > self.ttn:
        #     lumin = 90
        # else:
        #     lumin = 150

        if int(time()) > self.ttd:
            self.ttd = int(time()) + 10
        else:
            return

        if lumin > self.THR_LUMIN:
            self.dim = True

        print("New Ad")
        print params, len(bodies), len(faces)
        if len(bodies) == 1 or len(faces) == 1:
            if lumin > self.THR_LUMIN:
                if  temp < self.THR_TEMP:
                    self.ad = "people.jpeg"
                    self.send()
                    return
                if temp >= self.THR_TEMP:
                    self.ad = "warm.jpeg"
                    self.send()
                    return
        elif len(bodies) > 1 or len(faces) > 1:
            if lumin < self.THR_LUMIN:
                if temp < self.THR_TEMP:
                    self.ad = "rainy.jpeg"
                    self.send()
                    return
                elif temp >= self.THR_TEMP:
                    self.ad =  "default.jpeg"
                    self.send()
                    return
        self.ad = "aalto.jpeg"
        self.send()
        return

    def send(self):
        for d in self.dest:
            url = "http://"+d+":8080"
            files = {'file': ('ad.jpeg', open(self.ad,'rb'))}
            r = requests.put(url, files=files)
            #print r
        return


def main():
    #source = 0
    source = "http://192.168.1.79:8081"
    video_getter = VideoGet(source).start()
    sensor_getter = SensorGet()
    fp = FrameProcessor()
    ad_getter = AdGet()
    while True:
        if (cv2.waitKey(1) == ord("q")) or video_getter.stopped:
            video_getter.stop()
            break

        frame = video_getter.frame
        #cv2.imshow("Video", frame)
        bodies = fp.getBodies(frame)
        faces = fp.getFaces(frame)
        sensor_getter.get()
        params = [
        sensor_getter.lumin,sensor_getter.temperature, sensor_getter.humidity
        ]
        ad_getter.get(params, faces, bodies)
        cv2.imshow("ad", cv2.imread(ad_getter.ad))


if __name__ == '__main__':
    main()
