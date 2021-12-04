#!/bin/bash

path=${1:-"/home/pi/Music/musicSD/"}

while true;
do
	bash /home/pi/audio/hal/scripts/random_song.sh $path
done
