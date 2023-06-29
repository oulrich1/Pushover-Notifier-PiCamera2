
#!/usr/bin/python3

import time

import numpy as np

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

from pydub import AudioSegment
from pydub.playback import play

import http.client, urllib

class PushoverPoster:
    def __init__(self):
        pass

    def post_message():
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
          urllib.parse.urlencode({
            "token": "APP_TOKEN",
            "user": "USER_KEY",
            "message": "hello world",
          }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()


class MyAudio:
    def __init__(self, sound_file):
        format = sound_file.split('.')[-1]
        self.sound = AudioSegment.from_file(sound_file, format=format)

    def play_sound(self):
        print("playing sound")
        play(self.sound)

audio_file = "524345__javierserrat__pigeon.mp3"
audio = MyAudio(f'audio/mp3_tracks/{audio_file}')


class MotionDetector():
    def __init__(self):
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


    def motion_detected(self, mse):
        if not self.encoding:
            self.encoder.output = FileOutput(f"video/recordings/{int(time.time())}.h264")
            self.picam2.start_encoder()
            self.encoding = True
            print("New Motion", mse)
            audio.play_sound()
        self.ltime = time.time()

    def motion_stopped(self, mse):
        if self.encoding and time.time() - self.ltime > 2.0:
            self.picam2.stop_encoder()
            print("Motion Stopped", mse)
            self.encoding = False

    def detect_motion(self):
        prev = None
        while True:
            cur = self.picam2.capture_buffer("lores")
            cur = cur[:self.w * self.h].reshape(self.h, self.w)
            if prev is not None:
                # Measure pixels differences between current and previous frame
                mse = np.square(np.subtract(cur, prev)).mean()
                if mse > 8:
                    self.motion_detected(mse)
                else:
                    self.motion_stopped(mse)
            prev = cur


motion = MotionDetector()
motion.detect_motion()

