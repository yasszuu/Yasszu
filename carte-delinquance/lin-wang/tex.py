import sys; sys.path.insert(0, '../hippo'); import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from grade import grade
ne = Image.open("../lion/NE1_HR_LC_SR_W_DR.tif"); hy = Image.open("../v2/HYP_HR_SR_OB_DR.tif")
L, R, T, B = 90, 126, 32, 18
box = (int((L+180)*60), int((90-T)*60), int((R+180)*60), int((90-B)*60))
reg = Image.fromarray(grade(np.array(ne.crop(box)), np.array(hy.convert("RGB").crop(box))))
reg.resize((reg.width*2, reg.height*2), Image.LANCZOS).save("tex_region.jpg", quality=90); print(reg.size)
