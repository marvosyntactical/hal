from typing import List, Dict, Optional

import random
import subprocess
from subprocess import signal
import os
from time import sleep
import numpy as np
import math

from GPTJ.gptj_api import Completion

from automaton import VoiceControlledAutomaton, State, Exit, DEBUG


class GPTState(State):
    norm = 2
    rhyme = 3
    watts = 4
    joke = 5

class GPTBot(VoiceControlledAutomaton):
    def __init__(self, **kwargs):
        super().__init__(name="gpt bot", **kwargs)

        self.keywords = [
            "funny",
            "serious",
            "watts",
            "rhyme",
            "joke",
            "norm",
            "options",
            "enough",
        ]

        self.temperature = 1.0 # initially serious

        self.examples = {
            GPTState.rhyme: {
                "when it chimes": "it rhymes",
                "most of this meal is old and cooked": "just like its cook who is bold and crooked",
                "what do you say to such things": "they simply are what life brings",
                "any thoughts on this wine": "it is very fine to dine",
            },
            GPTState.joke: {
            },
            GPTState.norm: {
                "huh": "How many comedians does it take to change a lightbulb? Five, one to do it, and the others to say 'How long's he been up there?'",
                "Anyways": "Here's a really easy way to figure out if you're taking too many meds: You refer to your medication as 'meds'.",
                "now's the section where we do jokes": "Artifacts from Auschwitz are set to go on tour for the first time. Experts believe this will be Miley Cyrus' darkest opening act yet.",
                "what's new with you": "I've never gotten a decent explanation as to how Popeye the Sailor Man lost his eye.",
             "how are you": "A recent report stated that there are over 65 active serial killers in the United States. What they don't know, is there's actually 66! (laugh maniacially) ...that's just between you and me",
            "hey": "A Florida university student was caught streaking on campus and apparently told police he was on acid, and asked them to cut his dick off. Boy, these kids today are crazy, back in my day we didn't need drugs, we would just cut our own dicks off.",
            "hi": "I used to think revenge was a dish best served cold, but then I realized it meant 'getting back at somebody'.",
            "what's up": "I realized in therapy that I'm not afraid of dying, I'm afraid of living. Oh no, I'm afraid of dying!",
            "ey": "A penny earned is nothing to brag about.",
            "yo": "I signed up for my company's 401k but I don't think I can run that far.",
            "man": "Why is taking no pleasure in things I used to enjoy a sign of depression? Maybe I'm just finally sick of crayoning!",
            "eh": "To me perfect sex is like a carwash: You start by lining up right and going in slow and you finish when three Mexican dudes run up and furiously towel you off.",
            "now now": "I wouldn't call myself a fan of 'steampunk', but I will say it's the healthiest way to prepare punk.",
            },
            GPTState.watts: {
            }
        }
        self.contexts = {
            GPTState.rhyme: \
            """
These are some rhymes. They are classical limericks, the last two words of both lines always rhyme, with a stress on the last syllables.
            """,
            GPTState.joke: \
"""
This is some of the best dark humor to be found on /b/.
If you look over the fact theyre all written by the hacker named 4chan,
these are pretty damn good.
""",
            # from https://www.normjokes.com/:
            GPTState.norm: \
"""
These are a collection of jokes by comedian Norm MacDonald.
Norm was a beloved man of the people, a fellow like you and me.
Some of these remarks are left over from the time he did Weekend update,
others come from Norm MacDonald Live (NML).
These are crowd favorites, but more of a collection of comments, really.
""",
            GPTState.watts: \
"""
This thread contains a list of wisdoms by Philosopher Alan Watts.
He was influenced a lot by Eastern Philosophy, and brought many wisdoms
from the far east into Western Popular Culture. He can be considered a sage
conveying the wisdoms of the Buddha, Chinese and Japanese Masters.
"""
        }

        self.state_keywords = {
            GPTState.enter: self.keywords,
            GPTState.exit: [],
        }
        self.SideEffectTransitionMatrix = {
            GPTState.enter: self.react_to_choice,
            GPTState.norm: self.converse,
            GPTState.rhyme: self.converse,
            GPTState.joke: self.converse,
            GPTState.watts: self.converse,
            GPTState.exit: self.exit,
        }

        self._converse_max_tokens = {
            GPTState.norm: 200,
            GPTState.joke: 100,
            GPTState.rhyme: 20,
            GPTState.watts: 100,
        }

    def init_gptj_context(self, state: Optional[GPTState]=None):
        print("Loading gptj")
        state = state if state is not None else self.state # ONLY INITS MODEL FOR CURRENT STATE
        self.gptj_context = Completion(
            self.contexts[state],
            self.examples[state],
        )
        print("Loaded gptj")

    def set_temperature(self, be_serious: bool):
        if be_serious:
            self.temperature = 1.0
        else:
            # be more random
            self.temperature = 0.6


    def converse(self, prompt: str) -> GPTState:
        print("You: ", prompt)

        max_tokens = self._converse_max_tokens[self.state]

        response = self.gptj_context.completion(
            prompt,
            # user=User,
            # bot=Bot,
            max_tokens=max_tokens,
            temperature=self.temperature,
            top_p=1.0
        )
        print("Bot: ", response)
        self.speak(response)

        # add prompt to examples for memory!
        self.examples[self.state].update(
            {prompt: response}
        )

        return self.state

    def _parse_choice(self, choice: str, must_understand=False) -> Optional[GPTState]:
        if "serious" in choice:
            self.set_temperature(True)
            self.speak("Okay, let's keep it real from now on.")

        if "funny" in choice:
            self.set_temperature(False)
            self.speak(f"Alright, i'll be a bit more random, temperature set to {self.temperature}")

        if "norm" in choice:
            state = GPTState.norm
            self.init_gptj_context(state)
        elif "rhyme" in choice:
            state = GPTState.rhyme
            self.init_gptj_context(state)
        elif "watts" in choice:
            state = GPTState.watts
            self.init_gptj_context(state)
        elif "enough" in choice:
            state = GPTState.exit
        elif "remind" in choice or "help" in choice \
            or "options" in choice:
            self.remind_options()
            state = None
        else:
            if must_understand:
                # self.speak("You said: " + choice)
                print("You said: " + choice)
                print("Thats not an option right now. Please try again.")
                # self.speak("Thats not an option right now. Please try again.")
            state = None
        return state




