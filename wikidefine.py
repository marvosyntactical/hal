from typing import List, Dict, Optional

import random
import subprocess
from subprocess import signal
import os
from time import sleep
import numpy as np
import math

import wikipedia

from automaton import VoiceControlledAutomaton, State, Exit, DEBUG

class WikiBotState(State):
    pass

class WikiBot(VoiceControlledAutomaton):
    def __init__(self, **kwargs):
        super().__init__(name="wikibot", **kwargs)

        self.keywords = [
            "define",
        ]

        self.state_keywords = {
            WikiBotState.enter: self.keywords,
            WikiBotState.exit: [],
        }
        self.SideEffectTransitionMatrix = {
            WikiBotState.enter: self.define,
            WikiBotState.exit: self.exit,
        }

    def define(self, query: str, must_understand=False) -> Optional[WikiBotState]:
        query = query.replace("define", "", 1).strip()
        print("Wikibot query:", query)

        # via https://alanhylands.com/how-to-web-scrape-wikipedia-python-urllib-beautiful-soup-pandas/


        err = ""
        results = wikipedia.search(query)

        if not results:
            err = "Couldnt find an article matching "+ query

            self.exit(err)


        try:
            abstract = wikipedia.page(results[0]).summary
        except Exception as e:
            err = str(e)
            self.exit(err)

        print(abstract)
        self.speak(abstract)

        return WikiBotState.exit

    def _exit_effects(self, text: str):
        self.speak(text)


