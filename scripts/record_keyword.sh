#!/bin/bash

wavs="/home/pi/audio/wavs/"
name=${1:-"keyword"}
stub=${wavs}${name}
mono=${stub}_mono.wav
stereo=${stub}.wav

echo "==================================================="
echo "Recording keyword $name"
echo "Press Ctrl-C to end recording ..."

arecord -Dac108 -f S32_LE -r 16000 -c 4 $mono
echo "==================================================="
echo "Finished; converting to stereo ..."
sox $mono -c 2 $stereo
rm $mono
echo "==================================================="
echo "Finished; playing the keyword back ..."
aplay $stereo

echo "Keep? [y] or Discard [n]?"
read keep
if [ "$keep" == "n" ]; then
	rm $stereo
	echo "Discarded attempt."
fi
	

