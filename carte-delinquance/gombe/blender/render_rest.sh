#!/bin/sh
cd "$(dirname "$0")"
MISTF=0.25 SHOT=raid FRAMES=0,138 ../bl/bin/python shots.py $PWD/clips/raid 20 60 > r_raid.log 2>&1
SHOT=kalande FRAMES=0,138 ../bl/bin/python shots.py $PWD/clips/kalande 20 60 > r_kalande.log 2>&1
echo ok > r3d.done
