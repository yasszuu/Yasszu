# usage: sh sheet.sh "t1 t2 ..." (dans le dossier du projet) → snaps/check.jpg
node snap.js snap $1 2>&1 | grep -v CONSOLE | head -3
python3 -c "
from PIL import Image
ts='$1'.split(); n=len(ts); cols=6; rows=(n+cols-1)//cols
c=Image.new('RGB',(240*cols,427*rows))
for i,t in enumerate(ts): c.paste(Image.open(f'snaps/s-{float(t):.2f}.jpg').resize((240,427)),((i%cols)*240,(i//cols)*427))
c.save('snaps/check.jpg')"
