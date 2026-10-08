#!/bin/bash
# Renders every clip of the compilation: simulation dump, frames, then synced SFX.
cd "$(dirname "$0")"
PY=./venv/bin/python
i=0
for spec in 1:105 2:105 3:105 4:105 5:105 10:115 20:115 30:115 50:120 100:185; do
  n=${spec%%:*}; post=${spec##*:}
  side=$(( i % 2 == 0 ? 1 : -1 )); i=$((i+1))
  d=clips/c$n; mkdir -p $d
  echo "=== clip $n cuts (post $post, side $side) $(date +%T)"
  $PY watermelon.py --cuts $n --post $post --side $side --dump $d/motion.json >$d/dump.log 2>&1 || { echo "dump failed $n"; exit 1; }
  $PY sound.py $d/motion.json $d/sfx.wav >$d/sound.log 2>&1 || { echo "sound failed $n"; exit 1; }
  $PY watermelon.py --cuts $n --post $post --side $side --out $d/frames --res 576 1024 --samples 8 >$d/render.log 2>&1 || { echo "render failed $n"; exit 1; }
  echo "done clip $n: $(ls $d/frames | wc -l) frames $(date +%T)"
done
echo "ALL DONE"
