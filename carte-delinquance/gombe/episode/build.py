import json
s = open('src.html').read().replace('__TL__', open('timeline.json').read()).replace('__SHORE__', open('shore.json').read())
open('ep.html', 'w').write(s); print(len(s))
