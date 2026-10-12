#!/bin/sh
# rend les 3 plans 3D de l'anguille (540x960, 16 échantillons + débruitage) dans clips/<nom>/
cd "$(dirname "$0")"
for S in sargasses riviere abysse; do SHOT=$S ../bl/bin/python eel.py clips/$S 0 138 16 50 > r_$S.log 2>&1; done
echo done > r.done
