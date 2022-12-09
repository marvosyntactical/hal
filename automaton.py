from typing import List, Optional, Dict, Callable, Union
from subprocess import Popen
import logging
import os
import random

import speech_recognition as sr

from custom_recognizer import CustomRecognizer
from keywords import KeywordModel


DEBUG = 1
__all__ = ["State", "VoiceControlledAutomaton", "Exit"]

class State:
    # all subclass VCA FSA's states must inherit from this
    enter = 0
    exit = 1

class Exit(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        if self.args:
            self.text = args[0]
        else:
            self.text = ""

    def __bool__(self):
        return bool(self.text)

class VoiceControlledAutomaton:
    """
    A Voice Controlled
    Finite State Automaton.
    States may be VCAs as well.

    NOTE
    A singular underscore ("_") at beginning of method
    denotes not privacy/visibility, but that this method should be
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
        sound_dir="./wavs/",
        kw_model_path: str="/home/pi/audio/hal/models/audio_model_fp32.pt",
        n_keywords: int=8,
        sampling_rate: int=16000,
        log_automaton_utterances: bool=True,
        log_user_utterances: bool=True,
        **kwargs
    ):
        kwargs["_super"] = self
        """Subclass inits should first call super init, then append to self.keywords"""
        self.mic_index = int(mic_index)
        self.sound_dir = str(sound_dir)
        self.super = None

        self.keywords: List[List[str]] = []
        if _super is not None:
            self.super = _super
            assert isinstance(_super, VoiceControlledAutomaton)
            self.keywords += _super.keywords
            self.kw_model = _super.kw_model
            self.R = _super.R
            self.name = name
            self.logger = _super.logger
            self.log_user_utterances = _super.log_user_utterances
            self.log_automaton_utterances = _super.log_automaton_utterances
        else:
            self.R = CustomRecognizer()
            self.name = name
            self.logger = logging.getLogger(name=self.name)
            self.logger.setLevel(logging.INFO)
            if DEBUG: kw_model_path = None
            self.kw_model = KeywordModel(model_path=kw_model_path)
            self.log_user_utterances = log_user_utterances
            self.log_automaton_utterances = log_automaton_utterances

        # initial state, may be overwritten by subclasses
        self.set_state(State.enter)

        # which function to call depending on own state
        self.SideEffectTransitionMatrix: Dict[State, Callable[str, Union[State, Exit]]] = NotImplemented
        self.state_keywords: Dict[State, List[List[str]]] = NotImplemented


    # def load_keyword_model(self):
    #     """
    #     load model, dependent on self.state and self.keywords
    #     """ 
    #     raise NotImplementedError
    #     model_path = VoiceControlledAutomaton.kw_model_dir + self.name + VoiceControlledAutomaton.kw_model_ext 
    #     model = ...
    #     return model

    def play_sound(self, soundfile: str):

        f = os.path.join(self.sound_dir, soundfile+".mp3")

        if not os.path.exists(f):
            f = os.path.join(self.sound_dir, soundfile+".wav")
            Popen(["aplay", f])
        else:
            Popen(["mpg123", f]) #, close_fds=1)

    def speak(self, s, wait=True) -> None:
        say_process = Popen(["say", s], shell=False)
        if self.log_automaton_utterances:
            self.logger.info(s)
        if wait:
            say_process.wait()

    def keyword_transition(self) -> None:
        # listen to input and make state transition with side effects
        text = self.get_utterance(keyword=True)
        if type(text) != int:
            # within respond to input, we may enter a lower FSA
            self.transition(text)

    def transition(self, text):
        new_state = self.respond_to_input(text)
        self.set_state(new_state)
        # self.kw_model = self.load_keyword_model()
        return new_state

    def __call__(self, text):
        # start self.run after responding to text
        # (used by higher level FSA)
        self.transition(text)
        return self.run()

    def run(self):
        while True:
            try:
                self.keyword_transition()
            except Exit as couldnt_handle:
                print(f"{self} received Exit")
                # self.keyword_transition()
                self.reset()
                if self.super is not None:
                    print(f"{self} passes to super")
                    raise couldnt_handle
                else:
                    print(f"{self} passes")
                    pass

    def reset(self):
        self.state = State.enter

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
                if not DEBUG:
                    # TODO implement custom recognizer keyword model
                    audio = self.R.listen_from_keyword_on(
                        source,
                        keyword_model=self.kw_model
                    )
                else:
                    # while listen_from_keyword_on not impl, use this:
                    audio = self.R.listen(source)
            else:
                audio = self.R.listen(source)

            # got possibly empty/garbage audio by this point
            self.play_sound("blang")

        return audio

    def recognize(self, audio):
        try:
            text = self.R.recognize_google(audio).lower()
            # text = self.R.recognize_sphinx(audio).lower()

            self.play_sound("blung")
            # self.speak(random.choice([
            #     "alrighty",
            #     "alrighty",
            #     "okay",
            #     "ok",
            #     "gotcha",
            #     "gotchu",
            #     "k",
            #     "i am at your service"
            # ]))
            self.logger.info("got non-empty input: "+text)
            return text
        except sr.UnknownValueError:
            # empty/non-parseable utterance

            # err_msg = f"Repeat that, please."
            # self.speak(err_msg)
            # print(err_msg)
            return 1
        except sr.RequestError as e:
            self.logger.warn("Could not request results")
            return 2

    def get_utterance(self, keyword=True) -> str:
        audio = self.listen(for_keyword=keyword)
        text = self.recognize(audio)
        return text

    def exit(self, text: str) -> State:
        self._exit_effects(text)
        raise Exit(text)

    def _exit_effects(self, text):
        # overwrite me
        return

    def remind_options(self):
        if len(self.keywords) < 4:
            s = " or ".join(self.keywords) + "?"
        else:
            self.speak(f"{self} has the following options:")
            # self.speak("You can currently say one of the following:")
            s = ", ".join(self.keywords)

        self.speak(s)

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
        state = self._parse_choice(choice, must_understand=False)
        if state is None:
            # in this case, ask about desired activity
            # self.remind_options()

            # while True:
            #     choice = self.get_utterance(keyword=False)
            #     if type(choice) == int:
            #         pass
            #     else:
            #         state = self._parse_choice(choice, must_understand=True)
            #     # got a next state? -> exit loop
            #     if state is not None:
            #         break
            return self.state
        # self.play_sound("pling")

        self.set_state(state)
        return self.transition(choice)

    def set_state(self, state):
        self._set_state_effects(state)
        self.state = state

    def _set_state_effects(self, state):
        # overwrite me
        return

    def _parse_choice(self, text: str, must_understand:bool = False) -> Optional[State]:
        # overwrite me
        raise NotImplementedError

    def __str__(self):
        return self.name






