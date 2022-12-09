from typing import List, Dict, Optional

import random
import subprocess
from subprocess import signal
import os
from time import sleep
import numpy as np
import math
import json

from automaton import VoiceControlledAutomaton, State, Exit, DEBUG

from revChatGPT.revChatGPT import Chatbot as ChatGPT

# VCA code

class ChatState(State):
    pass

class ChatBot(VoiceControlledAutomaton):

    def __init__(self, **kwargs):
        super().__init__(name="chat gpt", **kwargs)

        self.SideEffectTransitionMatrix = {
            ChatState.enter: self.converse,
        }

        self.config_file = ".auth.json"

        self.init_chatgpt()

    def init_chatgpt(self):
        with open(self.config_file, "r") as auth:
            config = json.load(auth)

        self.chatbot = ChatGPT(config)

    def converse(self, prompt: str) -> ChatState:

        prompt = prompt.replace("chat", "").strip()

        print("="* 20)
        print("You:")
        print(prompt)
        print("="* 20)

        response = self.chatbot.get_chat_response(prompt)['message']

        print("+"* 20)
        print("ChatGPT:")
        print(response)
        print("+"* 20)

        self.speak(response)

        return self.state

