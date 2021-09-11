from typing import List, Dict, Optional


from .automaton import VoiceControlledAutomaton, State, Exit

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
            ["local"],
            ["shuffle"],
            ["youtube"],
            ["find", "a", "video"],
            ["next"],
            ["previous"],
            ["louder"],
            ["quieter"],
            ["pause"],
            ["enough"],
        ]
        # dictionary of possible keywords per state
        # (each state has a sublist of self.keywords as value)
        self.state_keywords: Dict[JukeBoxState, List[List[str]]] = {
            JukeBoxState.enter: self.keywords,
            JukeBoxState.exit: [],
            JukeBoxState.local: [
                ["local"],
                ["shuffle"],
                ["next"],
                ["louder"],
                ["quieter"],
                ["pause"],
                ["enough"],
            ],
            JukeBoxState.youtube: [
                ["youtube"],
                ["find", "a", "video"],
                ["next"],
                ["previous"],
                ["louder"],
                ["quieter"],
                ["pause"],
                ["enough"],
            ],
        }

        self.SideEffectTransitionMatrix = {
            JukeBoxState.enter: self.react_to_choice,
            JukeBoxState.exit: self.exit,
            JukeBoxState.local: self.respond_local,
            JukeBoxState.youtube: self.respond_youtube,
        }

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


 