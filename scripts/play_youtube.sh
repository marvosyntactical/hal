#!/bin/bash

videoId=$1
link="https://www.youtube.com/watch?v=${videoId}"

echo $link

cvlc --no-video $link
