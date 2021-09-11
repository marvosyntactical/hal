import sys
from subprocess import Popen

print(sys.argv)
videoId = sys.argv[1]

link=f"https://www.youtube.com/watch?v={videoId}"

print(videoId)
Popen(["cvlc", "--no-video", link])
