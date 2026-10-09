import sys, glob
from PIL import Image
d, out, w, h = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
fs = sorted(glob.glob(d + '/f*.jpg'))
ims = [Image.open(f).resize((w, h)) for f in fs]
cols = min(len(ims), 6)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (w * cols, h * rows))
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out, quality=90)
