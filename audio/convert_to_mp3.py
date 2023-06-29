import os
import glob
from pydub import AudioSegment

video_dir = '/home/pi/BigData/Projects/pimotion3/audio/raw_tracks'  # Path where the videos are located
extension_list = ('*.mp4', '*.flv', '*.wav', '*.m4a')

os.chdir(video_dir)
for extension in extension_list:
    for video in glob.glob(extension):
        mp3_filename = os.path.splitext(os.path.basename(video))[0] + '.mp3'
        print(video)
        print(mp3_filename)
        AudioSegment.from_file(video).export(f'../mp3_tracks/{mp3_filename}', format='mp3')
