from typing import List, Optional, Dict, Callable, Union
from subprocess import Popen
import logging
from enum import Enum

import speech_recognition as sr

from .custom_recognizer import CustomRecognizer

__all__ = ["State", "VoiceControlledAutomaton", "Exit"]

class State(Enum):
    # all subclass VCA FSA's states must inherit from this
    enter = 0
    exit = 1

class Exit(Exception):
    pass

class VoiceControlledAutomaton:
    """
    A Voice Controlled
    Finite State Automaton.
    States may be VCAs as well.

    NOTE
    A singular underscore ("_") at beginning of method
    denotes not privacy/visbility, but that this method should be
    overwritten by subclasses.
    ###########################
    TODO FIXME NOTE
    This object has more methods/attributes than necessary
    for an FSA. TODO clean up structure/make simpler
    ###########################
    """
    keyword_dir="/home/pi/audio/hal/keywords/",
    kw_model_dir="/home/pi/audio/hal/keywords/models/",
    kw_model_ext= ".pt"
    def __init__(
        self,
        _super = None,
        name = None,
        mic_index=1,
        **kwargs
    ):
        """Subclass inits should first call super init, then append to self.keywords"""
        self.mic_index = int(mic_index)
        
        self.keywords: List[List[str]] = []
        if _super is not None:
            assert isinstance(_super, VoiceControlledAutomaton)
            self.keywords += _super.keywords
            self.kw_model = _super.kw_model
            self.R = _super.R
            self.logger = _super.logger()
        else:
            self.R = CustomRecognizer()
            self.logger = logging.getLogger(name=name)
            self.logger.setLevel(logging.INFO)

        # initial state, may be overwritten by subclasses
        self.set_state(State.enter)

        self.SideEffectTransitionMatrix: Dict[State, Callable[str, Union[State, Exit]]] = {}
        self.state_keywords: Dict[State, List[List[str]]] = {}

    def load_keyword_model(self):
        """
        load model, dependent on self.state and self.keywords
        """ 
        raise NotImplementedError
        model_path = VoiceControlledAutomaton.kw_model_dir + self.name + VoiceControlledAutomaton.kw_model_ext 
        model = ...
        return model

    def speak(self, s, wait=False) -> None:
        Popen(["espeak", s], shell=wait)

    def get_utterance(self, keyword=True) -> str:
        audio = self.listen(for_keyword=keyword)
        text = self.recognize(audio)
        return text

    def keyword_transition(self) -> None:
        # listen to input and make state transition with side effects
        text = self.get_utterance(for_keyword=True)
        # within respond to input, we may enter a lower FSA
        self.transition(text)

    def transition(self, text):
        self.set_state(self.respond_to_input(text))
        self.kw_model = self.load_keyword_model()

    def __call__(self, text):
        # start self.run after responding to text
        # (used by higher level FSA)
        self.transition(text)
        self.run()

    def run(self):
        while True:
            try:
                self.transition()
            except Exit:
                break

    def respond_to_input(self, text):
        """
        Rule based side effects during state transition
        """
        new_state = self.SideEffectTransitionMatrix[self.state](text)
        return new_state

    def listen(self, for_keyword=True):
        with sr.Microphone(device_index=self.mic_index) as source:
            self.R.adjust_for_ambient_noise(source)
            self.logger.info("Waiting for voice input")

            if for_keyword:
                audio = self.R.listen_until_keyword(
                    source,
                    keyword_model=self.kw_model
                )   
            else:
                audio = self.R.listen(source)

            self.logger.info("got input")
        return audio

    def recognize(self, audio):
        try:
            text = self.R.recognize_google(audio).lower()
            return text
        except sr.UnknownValueError:
            self.speak("Speech Recognition could not understand")
            return 1
        except sr.RequestError as e:
            self.logger.warn("Could not request results")
            return 2

    def exit(self, text) -> State:
        self._exit_effects(text)
        raise Exit
    
    def _exit_effects(self, text):
        # overwrite me
        return

    def remind_options(self):
        self.speak("You can currently say one of the following:")
        s = " ".join([" ".join(kw) for kw in self.keywords])

    def react_to_choice(self, choice: str): 
        """
        After hearing the first keyword while waiting for a command, 
        The FSA can use this method to get the next state from 
        the choice on what to do,
        and then delegate the response to another function/method

        In other words, this may get called by VCA.respond_to_input
        (e.g. in the idle state), change the state, and call
        VCA.respond_to_input again
        """
        # see if initial utterance already contains valid choice
        state = self.parse_choice(choice, must_understand=False)
        if state is None:
            # in this case, ask about desired activity
            self.speak("What do you want to do?")
            self.remind_options()

            while True:
                choice = self.get_utterance(keyword=False)
                state = self._parse_choice(choice, must_understand=True)
                # got a next state? -> exit loop
                if state is not None:
                    break
        
        self.set_state(state)
        # now that we got the state, give that state the same utterance still
        return self.respond_to_input(choice)
    
    def set_state(self, state):
        self._set_state_effects(state)
        self.state = state

    def _set_state_effects(self, state):
        # overwrite me
        return
    
    def _parse_choice(self, text: str, must_understand:bool = False):
        # overwrite me
        raise NotImplementedError






