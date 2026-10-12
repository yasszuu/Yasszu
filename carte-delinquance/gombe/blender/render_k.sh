#!/bin/sh
cd "$(dirname "$0")"
SHOT=kalande FRAMES=0,138 ../bl/bin/python shots.py $PWD/clips/kalande 20 60 > r_kalande.log 2>&1
echo ok > r3d.done
