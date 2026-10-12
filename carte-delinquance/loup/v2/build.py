s = open('src.html').read().replace('__TL__', open('timeline.json').read()).replace('__HELPERS__', open('helpers.js').read())
open('page.html', 'w').write(s)
