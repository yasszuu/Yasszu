"""Prépare les textures satellite depuis Natural Earth (HYP_HR_SR_OB_DR, 21600x10800).
curl -LO https://naturalearth.s3.amazonaws.com/10m_raster/HYP_HR_SR_OB_DR.zip && unzip HYP_HR_SR_OB_DR.zip
"""
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None
im = Image.open("HYP_HR_SR_OB_DR.tif").convert("RGB")
im.resize((8192, 4096), Image.LANCZOS).save("tex_world.jpg", quality=90)
L, R, T, B = -14, 24, 60, 33          # doit correspondre à EU_BOX dans src.html
eu = im.crop((int((L+180)*60), int((90-T)*60), int((R+180)*60), int((90-B)*60)))
eu = eu.resize((eu.width*2, eu.height*2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
eu.save("tex_europe.jpg", quality=90)
