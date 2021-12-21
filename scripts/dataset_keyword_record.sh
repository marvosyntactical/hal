#!/bin/bash

label=${1:-"hal"}
wavs="data/hal_keywords/"$label"/"
# name=${2:-"keyword"}

# find running number of existing wavs
# wav file names: 01234.wav
max_file=$(ls $wavs | sort -n | tail -n 1)
max_index=${max_file%.*}
name=$((max_index+1))


stub=${wavs}${name}
mono=${stub}_mono.wav
stereo=${stub}.wav

echo "==================================================="
echo "Recording example $name for label $label"
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
	

