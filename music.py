from typing import List, Dict, Optional

import random
import subprocess
from subprocess import signal
import os
from time import sleep
import numpy as np
import math

from automaton import VoiceControlledAutomaton, State, Exit, DEBUG

# this module contains two voicecontrolledautomata:
# 1: jukebox; for playing music on disk
#

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

        # kwargs["_super"] = self # already done in automaton.py
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

    def _exit_effects(self, text):
        self.speak(f"Shutting down {self}.")

    def respond_local(self, text) -> JukeBoxState:
        couldnt_handle = self.LocalPlayer(text)
        if couldnt_handle:
             return self._parse_choice(couldnt_handle.text)
        return JukeBox.enter

    def respond_youtube(self, text) -> JukeBoxState:
        couldnt_handle = self.YoutubePlayer(text)
        return JukeBox.enter



class MusicPlayer:
    # abstract class containing 
    # commonoalities of LocalPlayer and YoutubePlayer APIs
    _playing = False
    def next(self):
        raise NotImplementedError
    def prev(self):
        raise NotImplementedError
    def pause(self):
        self._playing = False
    def play(self):
        self._playing = True

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
        super().__init__(name="local player", **kwargs)
        # list of all possible keywords
        # (each keyword is a list of tokens)
        self.keywords += [
            "play",
            # "pause",
            "shuffle",
            "let's start with",
            # "next",
            # "previous",
            "louder",
            "quieter",
            "enough",
        ]
        self.state_keywords: Dict[LocalMusicState, List[List[str]]] = {
            LocalMusicState.enter: self.keywords,
            LocalMusicState.shuffling: [
                "play", "pause", "resume", "next", "louder", "quieter", "enough"
            ],
            LocalMusicState.playing_list: [
                "play", "pause", "resume", "next", "previous", "louder", "quieter", "enough"
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
        # communicate with this process to manage music
        self.process: Optional[subprocess.Popen] = None

        self.dir = music_dir
        self.tracks = os.listdir(self.dir)
        self.shuffle_script_path = shuffle_script_path
        self.play_list_script_path = play_list_script_path
        self._sleep_time = 5 # seconds between re-check for process uptime

    def respond_while_playing_list(self, text):
        # TODO FIXME IMPLEMENT PLAYLISTS NOTE BUG
        self.speak("Playlists not implemented yet my man")
        return self.respond_while_shuffling(text)

    def respond_while_shuffling(self, text):
        state = self.state
        if not True in [kw in text for kw in
            self.state_keywords[LocalMusicState.shuffling]
        ]:
            # self.speak("That's not an option right now.")
            # self.speak("You can say one of the following:")
            # self.remind_options()
            # while True:
            #     choice = self.get_utterance(keyword=False)
            if not self._playing:
                self.start_shuffling(text.replace("shuffle","",1),end_proc=0)
        else:
            if "play" in text:
                self.logger.info("got request to play:", text)
                state = self.start_shuffling(text.replace("play","", 1), end_proc=1)
            elif "pause" in text:
                if not self._playing:
                    self.logger.info("got request to pause, but not playing: "+text)
                else:
                    self.pause() # MusicPlayer state change
                self.logger.info("got request to pause:", text)
                self.process.send_signal(signal.SIGSTOP)
            elif "resume" in text:
                if self._playing:
                    self.logger.info("got request to resume, but playing already: "+text)
                else:
                    self.play() # MusicPlayer state change
                self.process.send_signal(signal.SIGCONT)
            elif "next" in text:
                if self.process is None:
                    self.play()
                    state = self.start_shuffling()
                else:
                    if not self._playing:
                        self.play() # MusicPlayer state change
                        self.process.send_signal(signal.SIGCONT)
                    self.process.send_signal(signal.SIGINT)
            else:
                if DEBUG: print(self.name+" couldnt handle your request, exiting higher level FSA")
                if self.process is not None:
                    self.process.send_signal(signal.SIGTERM)
                raise Exit(text)

        return state

    def closest_match(self, query):
        # TODO efficiently find k closest matches in self.tracks 
        # via MED
        if DEBUG: print(f"{self} is finding closest match for '{query}'")

        def med_score(candidate, query):
            # copied from https://www.codespeedy.com/minimum-edit-distance-in-python/
            candidate = candidate.lower().strip()
            query = query.lower().strip()
            a, b = len(candidate), len(query)
            string_matrix = [[0 for i in range(b+1)] for i in range(a+1)]
            for i in range(a+1):
                for j in range(b+1):
                    if i == 0:
                        string_matrix[i][j] = j   # If first string is empty, insert all characters of second string into first.
                    elif j == 0:
                        string_matrix[i][j] = i   # If second string is empty, remove all characters of first string.
                    elif candidate[i-1] == query[j-1]:
                        string_matrix[i][j] = string_matrix[i-1][j-1]  # If last characters of two strings are same, nothing much to do. Ignore the last two characters and get the count of remaining strings.
                    else:
                        string_matrix[i][j] = 1 + min(string_matrix[i][j-1],      # insert operation
                        string_matrix[i-1][j],      # remove operation
                        string_matrix[i-1][j-1])    # replace operation
            med = string_matrix[a][b]

            # ======= some more hacky criteria ======

            score = med * 100
            # reward large fraction of query being found
            # TODO make this more precise:
            smooth=1
            score *= (smooth+b-len([c for c in query if c in candidate]))/b
            # keyword containment works decently
            for kw in query.split():
                if kw in candidate:
                    score *= 1/10
            # also reward long length
            # score *= a**(-(1/12))
            return score # lower is better

        i = -1
        top_score = float("inf")
        s = []
        for j, track in enumerate(self.tracks):
            score = med_score(track, query)
            if DEBUG:
                s.append((track,score))
            if score < top_score:
                top_score = score
                i = j
        candidate = self.tracks[i]

        if DEBUG:
            s_ = reversed(sorted(s, key=lambda tup: tup[1]))
            print("\n".join([
                f"{track[:30]} :\tS {round(score,4)},\tL {len(track)}"
                for (track, score) in s_
            ]))
            print("="*40)
            print("     ^^^^ TOP RESULTS ^^^^")

        dot = candidate.find(".")
        if dot == -1:
            pretty_candidate = candidate
        else:
            pretty_candidate = candidate[:dot]
        return candidate, pretty_candidate

    def play_track(self, track: str):
        while True:
            if self.process is None or self.process.poll() is not None:
                self.process = subprocess.Popen(["mpg123", os.path.join(self.dir, track)])
                self.play() # MusicPlayer state change
                break
            sleep(self._sleep_time)

    def start_shuffling(self, text, end_proc=False):
        # self.speak("Shuffling")
        # can either shuffle randomly or shuffle "after" playing desired first song
        if text: # "start with" in text:
            # TODO find music fuzzily with rest of text
            closest_track, pretty_cand = self.closest_match(text)

            self.speak("Alright, starting off with " + pretty_cand)
            self.logger.info("playing " + pretty_cand)
            if end_proc and self.process is not None:
                # end previous shuffle
                self.process.kill()
            self.play_track(closest_track)
        elif end_proc and self.process is not None:
            # end previous shuffle
            self.process.kill()

        while True:
            # start shuffling once current self.process is done
            if self.process is None or self.process.poll() is not None:
                self.process = subprocess.Popen(
                        ["bash", self.shuffle_script_path, self.dir],
                shell=1)
                self.play() # MusicPlayer state change
                break
            sleep(self._sleep_time)

        return LocalMusicState.shuffling

    def start_playing_list(self, text):
        self.speak("Playing your music in order.")
        while True:
            # start shuffling once current self.process is done
            if self.process is None or self.process.poll() is not None:
                self.process = subprocess.Popen(["bash", self.play_list_script_path], shell=1)
                self.play() # MusicPlayer state change
                break
            sleep(5)

        return LocalMusicState.playing_list

    def _parse_choice(self, choice: str, must_understand=False) -> Optional[JukeBoxState]:
        print(f"local music player in state={self.state} parsing choice={choice}")
        if "shuffle" in choice or "play" in choice:
            state = LocalMusicState.shuffling
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
        return state

    def next(self):
        raise NotImplementedError
    def prev(self):
        raise NotImplementedError

class YoutubeMusicState(State):
    playing = 2

class YoutubePlayer(VoiceControlledAutomaton, MusicPlayer):
    search_script_path="scripts/search_youtube.sh"
    play_script_path="scripts/play_youtube.sh"
    def __init__(
            self,
            **kwargs
        ):
        super().__init__(name="youtube player", **kwargs)

        self.keywords += [
            "find a video",
            "next",
            "previous",
            "louder",
            "quieter",
            "pause",
            "stop",
            "enough",
        ]
        self.state_keywords: Dict[YoutubeMusicState, List[str]] = {
            YoutubeMusicState.enter: self.keywords,
            YoutubeMusicState.playing: [
                "play", "pause", "next", "previous", "louder", "quieter", "stop", "enough"
            ],
            YoutubeMusicState.exit: [],
        }

        self.SideEffectTransitionMatrix = {
            YoutubeMusicState.enter: self.react_to_choice,
            YoutubeMusicState.playing: self.respond_while_playing,
            YoutubeMusicState.exit: self.exit,
        }

        self.volume = self.get_sys_volume()
        self.process: Optional[subprocess.Popen] = None

        self.top_ids_last_search: List[str] = []

        # TODO
        # self.search_script_path = search_script_path
        # self.play_script_path = play_script_path

    def search(self, query, topk=5):
        top_result_ids = subprocess.Popen(
            ["bash", self.search_script_path,
            str(topk),
            *query.split(" ")],
            stdout=subprocess.PIPE, stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        top_ids = list(reversed([ID.decode("utf-8") for ID in top_result_ids.stdout]))
        return top_ids

    def play_video(self, videoId: str):
        if DEBUG: print(f"playing https://www.youtube.com/watch?v="+videoId)
        self.process = subprocess.Popen(
            ["bash", self.play_script_path, videoId],
            stdout=subprocess.PIPE, # stdin=subprocess.PIPE,
            # stderr=subprocess.STDOUT
        )
        if DEBUG:
            while 1:
                sleep(5)
                print("process poll:")
                print(self.process.poll())
                print(self.process.stdout.read())
                print("\nsubprocess output ^")

    def _parse_choice(self, choice: str, must_understand=False) -> Optional[YoutubeMusicState]:
        print(f"YMP(state={self.state}) parsing choice {choice}")
        if "find" in choice or "search" in choice or "play" in choice:
            state = YoutubeMusicState.playing
        elif "list" in choice:
            state = YoutubeMusicState.start_playing_list
        elif "enough" in choice:
            state = YoutubeMusicState.exit
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

    def start_playing(self, text:str, video_id: Optional[str]=None, end_proc=False):
        if video_id:
            self.play_video(video_id)
        elif text: # "start with" in text:
            self.top_ids_last_search = self.search(text)

            if end_proc and self.process is not None:
                # end previous playing
                self.process.kill()
            self.play_video(self.top_ids_last_search.pop(0))
        elif end_proc and self.process is not None:
            # end previous playing
            self.process.kill()

        return YoutubeMusicState.playing

    def respond_while_playing(self, text):
        print(f"YMP(state={self.state}) parsing choice {text}")
        state = self.state
        if not True in [kw in text for kw in
            self.state_keywords[YoutubeMusicState.playing]
        ]:
            rtext = text.replace("find","",1).replace("search","",1)
            self.start_playing(rtext,end_proc=0)
        else:
            if "play" in text or "find" in text or "search" in text:
                self.logger.info("got request to play:", text)
                state = self.start_playing(text.replace("play","", 0), end_proc=1)
            elif "pause" in text:
                if not self._playing:
                    self.logger.info("got request to pause, but not playing: "+text)
                else:
                    self.pause() # MusicPlayer state change
                self.logger.info("got request to pause:", text)
                self.process.send_signal(signal.SIGSTOP)
            elif "resume" in text:
                if self._playing:
                    self.logger.info("got request to resume, but playing already: "+text)
                else:
                    self.play() # MusicPlayer state change
                self.process.send_signal(signal.SIGCONT)
            elif "next" in text:
                if self.process is None:
                    state = self.start_playing()
                else:
                    self.process.kill()
                    self.start_playing(video_id=self.top_ids_last_search.pop(0))
            else:
                if DEBUG: print(self.name+" couldnt handle your request, exiting higher level FSA")
                if self.process is not None:
                    self.process.send_signal(signal.SIGTERM)
                raise Exit(text)

        return state




