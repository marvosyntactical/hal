# entered with listen, recognize, and main from:
# https://iotdesignpro.com/projects/speech-recognition-on-raspberry-pi-for-voice-controlled-home-automation

from typing import List, Dict, Optional
from subprocess import Popen
import logging
import random

from custom_recognizer import CustomRecognizer
from automaton import VoiceControlledAutomaton, State, Exit

from music import JukeBox
from wikidefine import WikiBot
from gpt import GPTBot
from chat import ChatBot

# # TODO FIXME import these from their files after implementing
# VC_GPT = ...
# VC_Search = ...
# VC_Weather = ...
# VC_GPS = ...
VC_Pizza = ...

class HalState(State):
    """bot functionalities"""
    music = 2
    gpt = 3
    search = 4
    weather = 5
    gps = 6
    pizza = 7
    define = 8
    chat = 9

class Hal9k(VoiceControlledAutomaton):
    """
    Finite state automaton speech bot
    in each HalState, input is managed by a corresponding instance of a VoiceControlledFSA subclass
    """
    def __init__(
            self,
            **kwargs
        ):
        super().__init__(name="hal", **kwargs)
        # list of all possible keywords
        # (each keyword is a list of tokens)
        self.keywords += [
            "hey hal",
            "yo hal"
            "music",
            "jukebox",
            "gpt",
            "talk",
            "search",
            "define",
            "weather",
            "gps",
            "let's chat",
            "pizza",
            "options",
        ]
        # dictionary of possible keywords per state
        # (each state has a sublist of self.keywords as value)
        self.state_keywords: Dict[HalState, List[List[str]]] = {
            HalState.enter: self.keywords,
            HalState.exit: [],
            # HalState.music,
            # HalState.gpt,
            # HalState.search,
            # HalState.weather,
            # HalState.gps,
            # HalState.pizza,
        }

        self.SideEffectTransitionMatrix = {
            HalState.enter: self._respond_waiting,
            HalState.exit: self.exit,
            HalState.music: self.respond_music,
            HalState.gpt: self.respond_gpt,
            HalState.chat: self.respond_chat,
            HalState.define: self.respond_define,
        }

        self.MP = JukeBox(
            _super=self,
            **kwargs
        )
        self.WB = WikiBot(
            _super=self,
            **kwargs
        )
        self.GPT = GPTBot(
            _super=self,
            **kwargs
        )
        self.Chat = ChatBot(
            _super=self,
            **kwargs
        )
        # self.Weather = VC_Weather(
        #     **kwargs
        # )
        # self.GPS = VC_GPS(
        #     **kwargs
        # )
        # self.Pizza = VC_Pizza(
        #     **kwargs
        # )

    def _respond_waiting(self, text: str) -> HalState:
        greeting = random.choice([
            "Hi Marv.",
            "Whats up."
        ])
        self.speak(greeting)
        return self.react_to_choice(text)

    def _parse_choice(self, choice: str, must_understand=False) -> Optional[HalState]:
        if "music" in choice or "play" in choice or "juke" in choice:
            state = HalState.music
        elif "gpt" in choice or "talk" in choice:
            state = HalState.gpt
        elif "chat" in choice or "simsalabim" in choice:
            state = HalState.chat
        elif "search" in choice:
            state = HalState.search
        elif "define" in choice:
            state = HalState.define
        elif "weather" in choice:
            state = HalState.weather
        elif "gps" in choice:
            state = HalState.gps
        elif "pizza" in choice:
            state = HalState.pizza
        elif "exit" in choice or "bye" in choice:
            state = HalState.exit
        elif "remind" in choice or "help" in choice \
            or "options" in choice:
            self.remind_options()
            state = None
        else:
            if must_understand:
                self.speak("You said: " + choice)
                self.speak("Thats not an option right now. Please try again.")
            state = None
        return state

    def _exit_effects(self, text) -> None:
        self.speak("Goodbye.")

    def respond_music(self, text) -> HalState:
        """
        run Music Player; a lower FSA
        after exiting, return to hal's starting state again
        """
        self.MP(text)
        return HalState.enter

    def respond_define(self, text) -> HalState:
        """
        run Wiki Bot ; a lower FSA
        after exiting, return to hal's starting state again
        """
        self.WB(text)
        return HalState.enter

    def respond_gpt(self, text) -> HalState:
        self.GPT(text)
        return HalState.enter

    def respond_chat(self, text) -> HalState:
        self.Chat(text)
        return HalState.enter


if __name__ == "__main__":

    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    hal = Hal9k()
    hal.run()

