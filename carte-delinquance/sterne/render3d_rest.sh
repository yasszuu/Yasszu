#!/bin/sh
# attend la fin du plan Groenland, puis rend océan et Antarctique
cd "$(dirname "$0")"
while pgrep -f "shot.py ep/clips/groenland" >/dev/null; do sleep 10; done
for S in ocean:132 antarctique:138; do n=${S%%:*}; f=${S##*:}
  SHOT=$n ../bl/bin/python shot.py ep/clips/$n 0 $f 16 50 > r3d_$n.log 2>&1
done
echo done > r3d.done
