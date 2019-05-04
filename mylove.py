from threading import Thread
import cv2
from influxdb import InfluxDBClient
from time import time
import os
import numpy as np
import subprocess


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
        self.lumin = self.humidity = self.temperature = 0

    def get(self):
        result = self.client_pi.query('select luminosity, humidity, temperature from piroommonitor order by time desc limit 1 ')
        for res in result:
            for entry in res:
                self.temperature = entry['temperature']
                self.humidity = entry['humidity']
                self.lumin = entry['luminosity']

class FrameProcessor:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(os.path.join('haarcascade_frontalface_default.xml'))
        self.person_cascade = cv2.CascadeClassifier(os.path.join('haarcascade_fullbody.xml'))

    def getBodies(self, frame):
        bodies = []
        frame = cv2.resize(frame,(640,360)) # Downscale to improve frame rate
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) # Haar-cascade classifier needs a grayscale image
        bodies_scale = self.person_cascade.detectMultiScale(gray_frame)
        for (x, y, w, h) in bodies_scale:
            bodies.append(frame[y:y+h, x:x+w])
            cv2.imshow("bodies", bodies[-1])
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
        self.THR_TEMP = 10
        self.THR_LUMIN = 110
        self.ttd = int(time()) + 10
        self.ad = "default.jpeg"

    def get(self, params, faces, bodies):
        print self.ttd, int(time())
        self.dim = False
        lumin, temp, humid = params
        if lumin > self.THR_LUMIN:
            self.dim = True
        if int(time()) > self.ttd:
            self.ttd = int(time()) + 10
        else:
            return
        print("New Ad")
        print params
        if len(bodies) or len(faces):
            self.ad = "people.jpeg"
            return
        if temp > self.THR_TEMP:
            self.ad = "warm.jpeg"
        elif humid < self.THR_HUMIDITY:
            self.ad = "rainy.jpeg"
        else:
            self.ad =  "default.jpeg"
        return


class AdSend:
    def __init__(self):
        pass

    def send(ad, dest):
        pass

    def dim(dest):
        pass


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
