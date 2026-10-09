#!/bin/bash
# Gummy animal tower compilation: random event + random outcome per tier, then render + SFX.
cd "$(dirname "$0")"
PY=../venv/bin/python
for n in 1 3 5 10 20 30 50; do
  d=clips/t$n; mkdir -p $d
  echo "=== $n animals $(date +%T)"
  [ -f $d/sim.json ] || $PY tower_sim.py --n $n --out $d/sim.json 2>&1 | grep -v "build time" || { echo "sim failed $n"; exit 1; }
  $PY tower_sound.py $d/sim.json $d/sfx.wav >$d/sound.log 2>&1 || { echo "sound failed $n"; exit 1; }
  $PY tower_render.py $d/sim.json --out $d/frames --res 576 1024 --samples 10 >$d/render.log 2>&1 || { echo "render failed $n"; exit 1; }
  echo "done $n animals: $(ls $d/frames | wc -l) frames $(date +%T)"
done
echo "ALL DONE"
