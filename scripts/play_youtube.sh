#!/bin/bash

# this script receives input from STDIN (tail output)
# while read line; do
#    videoId=$line
# done
videoId=$1

echo "got video id:"
echo $videoId
template="https://www.youtube.com/watch?v="
link=$template$videoId

echo $link

# cvlc --no-video $link
cvlc --vout none $link
