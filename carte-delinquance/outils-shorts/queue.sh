while [ "$(ps -eo args | grep -c '^node snap.js frames')" != 0 ]; do sleep 10; done
sh render.sh ../sing singapour-la-ville-du-lion
sh render.sh ../ro roumanie-le-pays-des-ours
sh render.sh ../nz nouvelle-zelande-22-moutons
