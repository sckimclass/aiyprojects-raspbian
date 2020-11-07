#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A demo of the Google Assistant GRPC recognizer."""

import argparse
import locale
import logging
import signal
import sys
import time

from aiy.assistant import auth_helpers, device_helpers, action_helpers
import snowboydecoder

from aiy.assistant.grpc import AssistantServiceClientWithLed
from aiy.board import Board

import RPi.GPIO as GPIO
import time

def volume(string):
    value = int(string)
    if value < 0 or value > 100:
        raise argparse.ArgumentTypeError('Volume must be in [0...100] range.')
    return value

def locale_language():
    language, _ = locale.getdefaultlocale()
    return language

def main():
    logging.basicConfig(level=logging.DEBUG)
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))

    parser = argparse.ArgumentParser(description='Assistant service example.')
    parser.add_argument('--language', default=locale_language())
    parser.add_argument('--volume', type=volume, default=100)
    parser.add_argument('--model', default="resources/models/snowboy.umdl")
    args = parser.parse_args()

    credentials = auth_helpers.get_assistant_credentials()
    device_model_id, device_id = device_helpers.get_ids_for_service(credentials)
    device_handler = action_helpers.DeviceRequestHandler(device_id)

    GPIO.setmode(GPIO.BCM)
    LED = 17
    GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)

    @device_handler.command('com.example.commands.OnOff')
    def onoff(on):
        if on == "on":
            logging.info('Power on')
            GPIO.output(LED, GPIO.HIGH)
        elif on == "off":
            logging.info('Power off')
            GPIO.output(LED, GPIO.LOW)
            time.sleep(0.5)
            GPIO.output(LED, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(LED, GPIO.LOW)

    with Board() as board:
        assistant = AssistantServiceClientWithLed(board=board,
                                                  volume_percentage=args.volume,
                                                  language_code=args.language,
                                                  device_handler=device_handler)

        detector = snowboydecoder.HotwordDetector(args.model, sensitivity=0.5)

        while True:
            logging.info('Listening... Press Ctrl+C to exit')

            def detectedCallback():
                logging.info('Conversation started!')
                detector.terminate()

            detector.start(detected_callback=detectedCallback, sleep_time=0.03)

            assistant.conversation()

if __name__ == '__main__':
    main()
