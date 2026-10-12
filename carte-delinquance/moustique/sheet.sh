# planche contact : sheet.sh sortie.jpg t1 t2 ...
out=$1; shift; rm -f snap-*.jpg; node snap.js "$@" || exit 1
ls snap-*.jpg | sort -t- -k2 -g > list.txt
python3 - "$out" <<'PY'
import sys; from PIL import Image, ImageDraw
fs=[l.strip() for l in open('list.txt')]; ims=[Image.open(f) for f in fs]
w,h=270,480; cols=min(6,len(ims)); rows=(len(ims)+cols-1)//cols
sh=Image.new('RGB',(cols*w,rows*h),'black'); d=ImageDraw.Draw(sh)
for i,(f,im) in enumerate(zip(fs,ims)):
    im=im.resize((w,h)); x,y=(i%cols)*w,(i//cols)*h; sh.paste(im,(x,y)); d.text((x+6,y+6),f[5:-4],fill='yellow')
sh.save(sys.argv[1],quality=88)
PY
