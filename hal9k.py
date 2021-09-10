# started out from:
# https://iotdesignpro.com/projects/speech-recognition-on-raspberry-pi-for-voice-controlled-home-automation

from subprocess import Popen
import speech_recognition as sr
from custom_recognizer import CustomRecognizer
import serial
import RPi.GPIO as GPIO
import logging
from enum import Enum

class HalState(Enum):
    """bot functionalities"""
    waiting_for_activ = 0
    music_player = 1
    gpt = 2
    search = 3
    weather = 4
    gps = 5
    pizza = 6

class MPMode(Enum):
    """music functionalities"""
    waiting_for_input = 0
    local = 1 
    youtube = 2

class MPState(Enum):
    pause = 0
    playing = 1

class VoiceActivatedMP:
    """
    """
    def __init__():
        self.state = MPState.pause

    def __call__(self, text):
        pass
        

class Hal9k:
    """
    Finite state automaton speech bot
    """ 
    def __init__(
            self,
            MIC_INDEX=1,
            snowboy_dir="/home/pi/audio/snowboy/",
            pdml_dir="/home/pi/audio/SBpdmls/",
            **kwargs
        ):
        self.MIC_INDEX = MIC_INDEX

        self.R = CustomRecognizer()
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        self.StateResponse = {
            HalState.waiting_for_activ: self.respond_waiting,
            HalState.music_player: self.respond_music_player,
            HalState.gpt: self.respond_gpt,
        }

        # initial state
        self.state = HalState.waiting_for_activ

        self.MP = VoiceActivatedMP(
            **kwargs
        )
        self.GPT3Interface(
            **kwargs
        )

        self.snowboy_dir = snowboy_dir
        self.pdml_dir = pdml_dir
        # dict of hotword models, dependent on state
        self.state_to_hotwords = {
            HalState.waiting_for_activ: [
                "waiting"
            ],
            HalState.music_player: [
                "music"
            ],
            HalState.gpt: [
                "gpt"
            ],
        }
        self.pdml_ext = ".pdml"

    def _get_hotwords_pdmls(self):
        """
        dependent on self.state
        """ 
        pdmls = [
            self.pdml_dir + pdml + self.pdml_ext 
            for pdml in self.state_to_hotwords[self.state]
        ]
        return pdmls


    def boot(self, wait_for_keyword=True):
        # begin loop
        self.main_loop()

    def espeak(self, s, wait=False):
        return Popen(["espeak", s], shell=wait)

    def listen(self, snowboy=True):
        with sr.Microphone(device_index=self.MIC_INDEX) as source:
            self.R.adjust_for_ambient_noise(source)

            self.logger.info("Waiting for voice input")

            if snowboy:
                audio = self.R.listen(
                    source,
                    snowboy_configuration=(
                        self.snowboy_dir,
                        self._get_hotwords_pdmls(self.state)
                    )
                )   
            else:
                audio = self.R.listen(source)

            self.logger.info("got input")
        return audio

    def recognize(self, audio):
        try:
            text = self.R.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            self.espeak("Speech Recognition could not understand")
            return 1
        except sr.RequestError as e:
            self.logger.warn("Could not request results")
            return 2

    def main_loop(self):
        while 1:
            self.transition()

    def transition(self):
        audio = self.listen()
        text = self.recognize(audio)
        self.state = self.respond_to_input(text)

    def respond_to_global_keywords(self, text):
        return None

    def respond_to_input(self, text) -> HalState:
        """
        First:
        React to global keywords
        THen:
        Rule based state transitions
        """
        self.respond_to_global_keywords(text)

        new_state = self.StateResponse[self.state](text)
        return new_state

    def respond_waiting(self, text) -> HalState:
        assert False, text
        return

    def respond_music_player(self, text) -> HalState:
        """
        Music Player has its own set of states
        """
        state = self.MP(text)
        return state

    def respond_gpt(self, text) -> HalState:
        state = self.GPT3Interface(text)
        return state


        

if __name__ == "__main__":
    hal = Hal9k()
    hal.boot()
       
