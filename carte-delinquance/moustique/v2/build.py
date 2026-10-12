s = open('src.html').read().replace('__TL__', open('timeline.json').read()).replace('__HELPERS__', open('helpers.js').read()).replace('__DEPY__', open('assets/dep_years.json').read())
open('page.html', 'w').write(s)
