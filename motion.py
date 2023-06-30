
#!/usr/bin/python3

import os, time
import datetime as dt

import numpy as np

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

from pydub import AudioSegment
from pydub.playback import play

import http.client, urllib

from dotenv import load_dotenv
load_dotenv('.env.secret')


# https://stackoverflow.com/a/38836918/3277877
def isNowInTimePeriod(startTime, endTime, nowTime):
    if startTime < endTime:
        return nowTime >= startTime and nowTime <= endTime
    else:
        #Over midnight:
        return nowTime >= startTime or nowTime <= endTime


class PushoverPoster:
    def __init__(self):
        self.delay = 300
        self.ltime = time.time() - self.delay - 10

    def critical_message(self):
        if time.time() - self.ltime < self.delay:
            return None

        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
          urllib.parse.urlencode({
            "token": os.getenv('APP_TOKEN'),
            "user": os.getenv('USER_KEY'),
            "title": "Heather is Night Eating",
            "message": "Wake up! Heather is night eating!",
            "priority": 2,
            "retry": 30,
            "expire": self.delay,
          }), { "Content-type": "application/x-www-form-urlencoded" })
        res = conn.getresponse()
        self.ltime = time.time()
        return res


class MyAudio:
    def __init__(self, sound_file):
        format = sound_file.split('.')[-1]
        self.sound = AudioSegment.from_file(sound_file, format=format)

    def play_sound(self):
        play(self.sound)



class MotionDetector():
    def __init__(self, audio_file='pigeon-3.0.mp3'):
        self.picam2 = Picamera2()
        self.encoder = H264Encoder(1000000)

        lsize = (320, 240)
        self.w, self.h = lsize
        self.encoding = False
        self.ltime = 0

        video_config = self.picam2.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"},
                                                              lores={"size": lsize, "format": "YUV420"})
        self.picam2.configure(video_config)
        self.picam2.encoder = self.encoder
        self.picam2.start()

        self.pushover = PushoverPoster()
        self.audio = MyAudio(f'audio/mp3_tracks/{audio_file}')

    def notify(self):
        self.pushover.critical_message()
        self.audio.play_sound()

    def handle_motion_detected(self, mse):
        if not self.encoding:
            print("New Motion", mse)
            self.encoder.output = FileOutput(f"video/recordings/{int(time.time())}.h264")
            self.picam2.start_encoder()
            self.encoding = True
        print(f'> Motion Detected, {mse}')
        self.ltime = time.time()
        self.notify()

    def handle_motion_stopped(self, mse):
        if self.encoding and time.time() - self.ltime > 5.0:
            self.picam2.stop_encoder()
            print("Motion Stopped", mse)
            self.encoding = False

    def is_scheduled(self):
        return isNowInTimePeriod(dt.time(22,50), dt.time(4,1), dt.datetime.now().time())

    def is_motion_detected(self, mse):
        return mse > 18


    def detect_motion(self):
        prev = None
        while True:
            if not self.is_scheduled():
                sleep_time = 600
                print(f'Not Scheduled, sleeping {sleep_time}s')
                time.sleep(sleep_time)
                continue
            # time.sleep(1)
            cur = self.picam2.capture_buffer("lores")
            cur = cur[:self.w * self.h].reshape(self.h, self.w)
            if prev is not None:
                # Measure pixels differences between current and previous frame
                mse = np.square(np.subtract(cur, prev)).mean()
                if self.is_motion_detected(mse):
                    self.handle_motion_detected(mse)
                else:
                    self.handle_motion_stopped(mse)
                    time.sleep(1)
            prev = cur


motion = MotionDetector(audio_file='pigeon-3.0.mp3')
motion.detect_motion()

