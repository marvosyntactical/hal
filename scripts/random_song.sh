#!/bin/bash

music_dir=${1:-"/home/pi/Music/musicSD/"}
random_song=$(ls $music_dir | sort -R | tail -1)
mpg123 "${music_dir}${random_song}"
