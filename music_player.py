from enum import Enum
from .voice_controlled import VoiceControlled

class MPMode(Enum):
    """music functionalities"""
    waiting_for_input = 0
    local = 1 
    youtube = 2

class MPState(Enum):
    pause = 0
    playing = 1

class VC_MP(VoiceControlled):
    """
    """
    def __init__(self):
        self.state = MPState.pause

    def __call__(self, text):
        pass
 