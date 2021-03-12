import os
from PIL import Image
#import img2pdf
import requests
from io import BytesIO
import time

urls = open("C:\\Users\\5cent\\Desktop\\State_Papers_URLs_Final.txt",'r')

imgcount = 0
skipping = False
first = True
images = []
appending = False
for line in urls:
    if line.startswith('>'):
        #this is a new statepaper section. We will make a new directory.
        directory_name = line.split(':')[0][1:]
        #check if directory exists
        if os.path.exists(directory_name):
            continue        
        print("Making directory: {0}".format(directory_name))
        os.mkdir(directory_name)
        continue
    if line.startswith("#"):
        #this is a new volume, we need to save the current PDF
        #and start a new one
        li = line.split()
        new_pdf_name = directory_name+" "+li[0][1:]+" "+li[1]+".pdf"
        pdf_path = "./"+directory_name+"/"+directory_name+" "+li[0][1:]+" "+li[1]+".pdf"
        if os.path.exists(pdf_path):
            skipping = True
            continue
        skipping = False
        if not first:
            print("Finishing pdf: {0}".format(pdf_name))
            print("Wrote {0} images".format(imgcount))
        appending = False
        first = False
        pdf_name = new_pdf_name
        imgcount = 0
        print("Creating pdf: {0}".format(pdf_name))
        continue
    if line.startswith("http"):
        #line is a url
        if skipping:
            continue
        u = line.rstrip()
        response = requests.get(u)
        image = Image.open(BytesIO(response.content))
        image.load()
        time.sleep(2)
        imgcount += 1
        if appending:
            image.save(pdf_path, "PDF" ,resolution=100.0, save_all=True, append=True)
        else:
            image.save(pdf_path, "PDF" ,resolution=100.0, save_all=True, append=False)
        appending = True
         

pdf.close()
