# Revamp

## Keyword based Interaction

Goals:
1. Activate based on keywordmodel trained on voice.
2. Only then pass to google.
3. Avoid activation based on noise this way.
4. Make requested (loud) stuff run in background, and stay reactive

* [TODO] write method KWModel.infer(bytes) that transforms to tensor
* [TODO] go from bytestring waveform to tensor waveform
* [TODO] in sr, find how audioop converts bytes to floats
* [TODO] how to get stereo sr stream? is dataset in actual stereo?
* [TODO] speech recognition waveform type: pyaudio -> audioop byte fragment
* [TODO] pl waveform type: torchaudio.load output
* [TODO] 

## Dataset & Model
* [TODO] add background noise to dataset 

## Non-Keyword Interaction

* [TODO] fuck around
* [DONE] fix going back to super VCA not working (say "enough")
* [TODO] find out


# hal9k bot notes

* snowboy deprecated; write own keyword detector?
* listen doesnt wait

* keyword spotting: have list of keywords associated with each state
* inherit wider scope keywords from above
* load worst/smallest model trained on all the keywords of the new state when transitioning 

## Search gist

* search: youtube api -> bash scripts
* -> play using cvlc
* search: 
* "search for something please"
* starts playing 1st bad result -> "next"
* starts playing 2nd bad result -> "next"
* starts playing good result -> "perfect"
* -> continues playing, waiting for keyword


# Reminders/TODOs
* [TODO] think about how to implement keyword models
* [TODO] CR.listen_from_keyword: *start* listening from keyword on until pause!
* [TODO] keywords of various levels may not coincide (e.g. search/find a video) -> is there a way to solve this?
* [TODO] multiprocessing while still waiting for sub automaton run() methods?
* [TODO] transitioning to next state *before* reacting to input is sensible for transitioning from one to another bot functionality, but unintuitive for play/pause type state transitions
* [TODO] 
* [TODO] 
* [TODO] 
