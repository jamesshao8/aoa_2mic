"""
 Estimate time delay using GCC-PHAT 
 This code is modified and simplified based on Xiong Yihui's previous work

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import pyaudio
import numpy as np
import collections
import threading
import signal
import sys
import math
from gcc_phat import gcc_phat
import time


class Microphone:

    def __init__(self, rate=48000, channels=2):
        self.pyaudio_instance = pyaudio.PyAudio()
        self.queue = collections.deque(maxlen=10)
        self.channels = channels
        self.sample_rate = rate

        device_index=None

        if device_index is None:
            for i in range(self.pyaudio_instance.get_device_count()):
                dev = self.pyaudio_instance.get_device_info_by_index(i)
                name = dev['name'].encode('utf-8')
                print(i, name, dev['maxInputChannels'], dev['maxOutputChannels'])
                if dev['maxInputChannels'] == self.channels:
                    print('Use {}'.format(name))
                    device_index = i
                    break

            if device_index is None:
                print('can not find input device with {} channel(s)'.format(self.channels))
                return

        self.stream = self.pyaudio_instance.open(
            start=True,
            format=pyaudio.paInt16,
            input_device_index = device_index,
            channels=self.channels,
            rate=self.sample_rate,
            frames_per_buffer=320,
            stream_callback=self._callback,
            input=True,
            
        )


    def _callback(self, in_data, frame_count, time_info, status):
        self.queue.append(in_data)
        return None, pyaudio.paContinue

    def start(self):
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()


def main():
    sample_rate = 48000
    channels = 2

    mic = Microphone(sample_rate, channels)
    max_tau = 0.000166667


    while True:
        try:
            time.sleep(1)
            buf = b''.join(mic.queue)
            buf = np.fromstring(buf, dtype='int16')
            tau, _ = gcc_phat(buf[0::2], buf[1::2], fs=sample_rate, max_tau=max_tau,interp=1)
            theta = np.arcsin(tau / max_tau) * 180 / np.pi
            alpha = np.arccos(-tau / max_tau) * 180 / np.pi
            a = int(alpha)
            print "alpha:",str(a),"    tau:",tau
            #print "A:",np.max(buf[0::1]),"B:",np.max(buf[1::2])

        except KeyboardInterrupt:
            break

    mic.stop()

        
if __name__ == '__main__':
    main()
