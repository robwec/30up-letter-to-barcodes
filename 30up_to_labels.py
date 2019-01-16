import time
import os
import subprocess
import cv2
import numpy as np
from subprocess import call
#######
##utils
def showImage(myimage, mypath = "zzztestcoords.jpg", show = True):
	if mypath == None:
		mypath = "zzztestcoords.jpg"
	cv2.imwrite(mypath, myimage)
	if show:
		call("wine \"c:/Program Files/IrfanView/i_view64.exe\" + \"" +mypath+"\"", shell=True)
	return
def sshow(image, name = None, showit = True):
	if type(name) == type(None):
		showImage(recon(image), mypath = None, show = showit)
	else:
		showImage(recon(image), name, showit)
	return
def recon(myimage_float): #reconstitutes float images to uint8
	dst = np.empty(myimage_float.shape)
	#return np.round(cv2.normalize(myimage_float, dst = dst, alpha = 0, beta = 255, norm_type = cv2.NORM_MINMAX)).astype(np.uint8)
		#slow?
	return cv2.normalize(myimage_float, dst = dst, alpha = 0, beta = 255, norm_type = cv2.NORM_MINMAX).astype(np.uint8)

############
##main stuff
def explodeTargetPDF_makeTifs_gs(filename, outfolder):
	os.makedirs(outfolder, exist_ok = True)
	#make single-page tifs from full pdf
	time_start = time.time()
	cmd = "gs -q -dAutoRotatePages=/None -dPDFFitPage -dNOPAUSE -dQUIET -dBATCH -sDEVICE=tiffscaled -r300 -dCenterPages=true -sOutputFile=\"" + outfolder + "/page_%05d.tif\" \""+filename+"\""
	_ = subprocess.call(cmd, shell = True)
	time_end = time.time()
	print(round(time_end - time_start, 2), "seconds to split the PDF into tifs with ghostscript.")
	'''
	#dilate the tifs
	time_start = time.time()
	cmd = "for file in \""+outfolder+"/*.tif\"; do\n\tmogrify -negate -morphology dilate octagon:1 -negate \"$file\"\ndone"
	_ = subprocess.call(cmd, shell = True)
	time_end = time.time()
	print(round(time_end - time_start, 2), "seconds to dilate all the tifs.")
	'''
	return

def explodeTargetPDF_makePngs(filename, outfolder):
	os.makedirs(outfolder, exist_ok = True)
	#make single-page tifs from full pdf
	time_start = time.time()
	cmd = "gs -q -dAutoRotatePages=/None -dPDFFitPage -dNOPAUSE -dQUIET -dBATCH -sDEVICE=pngalpha -r600 -dCenterPages=true -sOutputFile=\"" + outfolder + "/page_%05d.png\" \""+filename+"\""
	_ = subprocess.call(cmd, shell = True)
	time_end = time.time()
	print(round(time_end - time_start, 2), "seconds to split the PDF into pngs with ghostscript.")
	return
def splitAllPageImages_intoLabels(infolder, outfolder):
	os.makedirs(outfolder, exist_ok = True)
	pages = os.listdir(infolder)
	pages = list(filter(lambda x: x.split(".")[-1] in ["png"], pages))
	pages = [infolder + "/" + x for x in pages]
	thislabelnum = 1
	time_start = time.time()
	for i in range(len(pages)):
		thislabelnum = extractLabels_fromPage(pages[i], thislabelnum, outfolder)
	time_end = time.time()
	print(round(time_end - time_start, 2), "seconds to split the pages into individual label pngs.")
	return

#600 DPI sheets, 6600 px x 5100 px
labelwidth = 1558
labelheight = 591
firstoffset_x = 59
firstoffset_y = 319
step_y = 600
step_x = 1667
def extractLabels_fromPage(mypage, thislabelnum, outfolder):
	pageim = cv2.imread(mypage) #(6600, 5100, 3) shape
	#30 positions. starts in top left, going down up to 10 rows, then right up to 3 columns. 10 rows 3 columns.
	blank = False
	pagepos = 0 #ends at 29
	while not blank and pagepos < 30:
		x_pos = pagepos // 10
		y_pos = pagepos % 10
		x_start = firstoffset_x + x_pos * step_x
		x_end = firstoffset_x + x_pos * step_x + labelwidth
		y_start = firstoffset_y + y_pos * step_y
		y_end = firstoffset_y + y_pos * step_y + labelheight
		thislabel_im = pageim[y_start:y_end, x_start:x_end].copy()
		if np.all([x == 255 for x in thislabel_im]): #blank label. stop.
			blank = True
			continue
		else:
			thislabel_im = boldThisLabelText(thislabel_im)
				#the first ~248px at the top is barcode, do not bold. Bold everything below that, though.
			outpath = outfolder+"/"+"label_"+str(thislabelnum).zfill(5)+".png"
			_ = cv2.imwrite(outpath, thislabel_im)
			pagepos += 1
			thislabelnum += 1
	return thislabelnum
def boldThisLabelText(thislabel_im):
	kernel = np.ones((3,3),np.uint8)
	dilation = cv2.erode(thislabel_im, kernel, iterations = 1)
	thislabel_im[248:] = dilation[248:]
	return thislabel_im

""" theoretically, I'd like to combine the images into a pdf, but this wasn't working and isn't really necessary because it's possible to print an entire directory of images.
def combineAllLabels(infolder):
	labels = os.listdir(infolder)
	labels = list(filter(lambda x: x.split(".")[-1] in ["png"], labels))
	labels = [infolder + "/" + x for x in labels]
	labels.sort()
	#convert 600DPI png to 203 DPI tif? actually, it seems fine as-is
	'''
	def resamp(x):
		outpath = ".".join(x.split(".")[:-1])+".tif"
		#call("convert -units PixelsPerInch \""+x+"\" -resample 203 \""+outpath+"\"", shell=True)
		call("convert \""+x+"\" \""+outpath+"\"", shell=True)
		return
	_ = [resamp(x) for x in labels]
	#convert tif to pdf... blah, this isn't working.
	def tif2pdf(x):
		inpath = ".".join(x.split(".")[:-1])+".tif"
		outpath = ".".join(x.split(".")[:-1])+".pdf"
		call("tiff2pdf \""+inpath+"\" -z -o \""+outpath+"\"", shell=True)
		return
	_ = [tif2pdf(x) for x in labels]
	#combine pdfs
	'''
	return
"""

def main(pdfname):
	os.makedirs("pages", exist_ok = True)
	os.makedirs("labels", exist_ok = True)
	#call(rm "labels/*.png", shell = True)
	_ = call("find ./pages -maxdepth 1 -type f -name \"*.png\" -delete", shell = True)
	_ = call("find ./labels -maxdepth 1 -type f -name \"*.png\" -delete", shell = True)
	#1: split to png. 600 DPI
	explodeTargetPDF_makePngs("products.pdf", "pages")
	#2: split pages into labels.
	splitAllPageImages_intoLabels("pages", "labels")
	#3: combine all labels into output PDF.
	#combineAllLabels("labels")
	#NOPE. don't even need to combine the images.
	return

#How to print a folder of images:
"""
Linux:
	lpstat -p -d
		to find your printer
		mine is Zebra-EPL2-Label
	lpr -P Zebra-EPL2-Label labels/*.png
		to print all the pages
	done.
"""

if __name__ == "__main__":
	main("products.pdf")

