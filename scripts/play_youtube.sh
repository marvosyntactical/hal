#!/bin/bash

videoId=$1
echo "got video id:"
echo $videoId
template="https://www.youtube.com/watch?v="
link=$template$videoId

echo $link

cvlc --no-video $link
