from typing import List, Dict, Optional

import random
import subprocess
import os
from time import sleep
import numpy as np

from automaton import VoiceControlledAutomaton, State, Exit

class JukeBoxState(State):
    """jukebox functionalities"""
    local = 2
    youtube = 3

class JukeBox(VoiceControlledAutomaton):
    """
    Finite state automaton speech bot
    """ 
    def __init__(
            self,
            **kwargs
        ):
        super().__init__(name="jukebox", **kwargs)
        # list of all possible keywords
        # (each keyword is a list of tokens)
        self.keywords += [
            "local",
            "youtube",
            "find a song"
        ]
        # dictionary of possible keywords per state
        # (each state has a sublist of self.keywords as value)
        self.state_keywords: Dict[JukeBoxState, List[List[str]]] = {
            JukeBoxState.enter: self.keywords,
            JukeBoxState.exit: [],
        }

        self.SideEffectTransitionMatrix = {
            JukeBoxState.enter: self.react_to_choice,
            JukeBoxState.exit: self.exit,
            JukeBoxState.local: self.respond_local,
            JukeBoxState.youtube: self.respond_youtube,
        }

        self.LocalPlayer = LocalPlayer(
            **kwargs,
        )
        self.YoutubePlayer = YoutubePlayer(
            **kwargs
        )

    def _parse_choice(self, choice: str, must_understand=False) -> Optional[JukeBoxState]:
        if "local" in choice or "shuffle" in choice:
            state = JukeBoxState.local
        elif "find" in choice or "youtube" in choice:
            state = JukeBoxState.youtube
        elif "enough" in choice:
            state = JukeBoxState.exit
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

    def exit_effects(self):
        self.speak("Shutting down music player.")

    def respond_local(self, text) -> JukeBoxState:
        self.LocalPlayer(text)
        return JukeBox.enter

    def respond_youtube(self, text) -> JukeBoxState:
        self.YoutubePlayer(text)
        return JukeBox.enter



class MusicPlayer:
    def next(self):
        raise NotImplementedError
    def prev(self):
        raise NotImplementedError
    def pause(self):
        raise NotImplementedError
    def play(self):
        raise NotImplementedError

    def adjust_volume(self, percent:int =5):
        curr_vol = self.get_sys_volume()
        self.set_sys_volume(curr_vol+percent)

    def get_sys_volume(self):
        # get current system volume
        volume_info = subprocess.Popen(
            ["amixer", "get", "Master"], stdout=subprocess.PIPE
        )
        for line in volume_info.stdout:
            pass
        s = line.decode("utf-8")
        brackets = s[s.find("["):s.find("]")]
        percentage = brackets.replace("[", "").replace("%", "")

    def set_sys_volume(self, volume: int):
        if volume < 0:
            volume = 0
        elif volume > 100:
            volume = 100
        subprocess.Popen(
            ["amixer", "set", "Master", f"{int(volume)}%"]
        )



class LocalMusicState(State):
    shuffling = 2
    playing_list = 3
    start_shuffling = 4
    start_playing_list = 5

class LocalPlayer(VoiceControlledAutomaton, MusicPlayer):
    def __init__(
            self,
            music_dir="/home/pi/Music/musicSD/",
            shuffle_script_path="/home/pi/audio/hal/scripts/shuffle.sh",
            play_list_script_path="/home/pi/audio/hal/scripts/play_list.sh",
            **kwargs
        ):
        super().__init__(name="local", **kwargs)
        # list of all possible keywords
        # (each keyword is a list of tokens)
        self.keywords += [
            "play",
            "pause",
            "shuffle",
            "let's start with",
            "next",
            "previous",
            "louder",
            "quieter",
            "enough",
        ]
        self.state_keywords: Dict[LocalMusicState, List[List[str]]] = {
            LocalMusicState.enter: self.keywords,
            LocalMusicState.shuffling: [
                "play", "pause", "next", "previous", "louder", "quieter", "enough"
            ],
            LocalMusicState.playing_list: [
                "play", "pause", "next", "previous", "louder", "quieter", "enough"
            ],
            LocalMusicState.exit: [],
        }

        self.SideEffectTransitionMatrix = {
            LocalMusicState.enter: self.react_to_choice,
            LocalMusicState.exit: self.exit,
            LocalMusicState.shuffling: self.respond_while_shuffling,
            LocalMusicState.playing_list: self.respond_while_playing_list,
        }

        self.volume = self.get_sys_volume()
        self.process: Optional[subprocess.Popen] = None

        self.dir = music_dir
        self.tracks = os.listdir(self.dir)
        self.shuffle_script_path = shuffle_script_path
        self.play_list_script_path = play_list_script_path

    def respond_while_playing_list(self, text):
        pass

    def respond_while_shuffling(self, text):
        if not True in [kw in text for kw in
            self.state_keywords[LocalMusicState.shuffling]
        ]:
            self.speak("That's not an option right now.")
            self.speak("You can say one of the following:")
            self.remind_options()
            while True:
                choice = self.get_utterance(keyword=False)

    def closest_match(self, query):
        # TODO efficiently find k closest matches in self.tracks 
        # via MED
        self.speak("Wait a second.")

        def med(s1, s2):
            
            m, n = len(s1), len(s2)
            # for all i and j, d[i,j] will hold the Levenshtein distance between
            # the first i characters of s and the first j characters of t
            d = np.zeros(m,n)
            
            # source prefixes can be transformed into empty string by
            # dropping all characters
            for i in range(1, m+1):
                d[i, 0] = i
            
            # target prefixes can be reached from empty source prefix
            # by inserting every character
            for j in range(1, n+1):
                d[0, j] = j
            
            for j in range(1, n+1):
                for i in range(1, m+1):
                    if s1[i] == s2[j]:
                        substitutionCost = 0
                    else:
                        substitutionCost = 1

                    d[i, j] = min(  d[i-1, j] + 1,                   # deletion
                                    d[i, j-1] + 1,                   # insertion
                                    d[i-1, j-1] + substitutionCost)  # substitution
            
            return d[m, n]

        i = -1
        top_score = float("inf")
        for j, track in enumerate(self.tracks):
            score = med(query, track)
            if score < top_score:
                top_score = score 
                i = j


        self.speak("Alright, playing " + candidate)

    def play_track(self, track: str):
        self.process = subprocess.Popen(["mpg123", os.path.join(self.dir, track)])

    def start_shuffling(self, text):
        self.speak("Shufflin'")
        # can either shuffle randomly or shuffle "after" playing desired first song
        if "start with" in text:
            # TODO find music fuzzily with rest of text
            uttered_track_name = text[text.find("with")+4:]
            closest_track = self.closest_match(uttered_track_name)
            self.play_track(closest_track)

        while True:
            # start shuffling once current self.process is done
            if self.process is None or self.process.poll() is not None:
                self.process = subprocess.Popen(["bash", self.shuffle_script_path], shell=1)
                break
            sleep(5)
        
        return LocalMusicState.shuffling

    def start_playing_list(self, text):
        self.speak("Playing your music in order.")
        while True:
            # start shuffling once current self.process is done
            if self.process is None or self.process.poll() is not None:
                self.process = subprocess.Popen(["bash", self.play_list_script_path], shell=1)
                break
            sleep(5)
 
        return LocalMusicState.playing_list
    
    def _parse_choice(self, choice: str, must_understand=False) -> Optional[JukeBoxState]:
        if "shuffle" in choice:
            state = LocalMusicState.start_shuffling
        elif "list" in choice: 
            state = LocalMusicState.start_playing_list
        elif "enough" in choice:
            state = LocalMusicState.exit
        elif "remind" in choice or "help" in choice \
            or "options" in choice:
            self.remind_options()
            state = None
        else:
            if must_understand:
                self.speak("You said: " + choice)
                self.speak("Thats not an option right now. Please try again.")
            state = None

    def next(self):
        raise NotImplementedError
    def prev(self):
        raise NotImplementedError
    def pause(self):
        raise NotImplementedError
    def play(self):
        raise NotImplementedError


class YoutubePlayer(VoiceControlledAutomaton, MusicPlayer):
    def __init__(
            self,
            **kwargs
        ):
        super().__init__(name="youtube", **kwargs)
        
        self.keywords += [
            "find a video",
            "next",
            "previous",
            "louder",
            "quieter",
            "pause",
            "enough",
        ]
        self.state_keywords: Dict[YoutubeMusicState, List[List[str]]] = {
            YoutubeMusicState.enter: self.keywords,
            YoutubeMusicState.playing: [
                "play", "pause", "next", "previous", "louder", "quieter", "enough"
            ],
            YoutubeMusicState.exit: [],
        }

        self.SideEffectTransitionMatrix = {
            YoutubeMusicState.enter: self.react_to_choice,
            YoutubeMusicState.exit: self.exit,
        }

        self.volume = self.get_sys_volume()
        self.process: Optional[subprocess.Popen] = None

        self.dir = music_dir
        self.tracks = os.listdir(self.dir)
        self.search_script_path = search_script_path
        self.play_script_path = play_script_path

    def search(self, query, topk=5):
        top_result_ids = Popen(
            ["bash", self.search_script_path, 
            str(topk),
            *query.split(" ")],
            stdout=subprocess.PIPE, stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        top_ids = reversed([ID.decode("utf-8") for ID in top_result_ids.stdout])
        return top_ids
    
    def play(self, videoId: str):
        self.process = Popen(
            ["bash", self.play_script_path, videoId],
            stdout=subprocess.PIPE, stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

    def _parse_choice(self, choice: str, must_understand=False) -> Optional[HalState]:
        if "shuffle" in choice:
            state = LocalMusicState.start_shuffling
        elif "list" in choice: 
            state = LocalMusicState.start_playing_list
        elif "enough" in choice:
            state = LocalMusicState.exit
        elif "remind" in choice or "help" in choice \
            or "options" in choice:
            self.remind_options()
            state = None
        else:
            if must_understand:
                self.speak("You said: " + choice)
                self.speak("Thats not an option right now. Please try again.")
            state = None

    def next(self):
        raise NotImplementedError
    def prev(self):
        raise NotImplementedError
    def pause(self):
        raise NotImplementedError
    def play(self):
        raise NotImplementedError

