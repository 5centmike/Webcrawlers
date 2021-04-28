from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, A4
#import  pyPDF2
from PIL import Image
from io import BytesIO
import sys
import os
import unidecode
import re
from PyPDF2 import PdfFileMerger, PdfFileReader


#what we do here is iterate through every directory,
#look for PDFtxt files.
#create a PDF using the metadata from the PDFtxt file and the jpgs,
#from the jpgs folder specified in the PDFtxt file.
#save that into that directory.

#specifically: we read in PDFtxt. We use ReportLba to open a Table of Contents Canvas
#and create a Canvas for every entry
#as well as a PDF of the images using PIL for every entry.
#we then use PyPDF2 to append all the PDFs in the correct order.

def Recurse(directory,jpgdirectory):
    li = os.listdir(directory)
    for entry in li:
        if entry == "PDFtxt.txt":
            size = os.path.getsize(directory+"\\"+entry)
            #print(os.path.getsize(directory+"\\"+entry))
            if size:
                #make PDf
                makePDF(directory,jpgdirectory)            
        #elif entry == "Metadata.txt":
        #    continue
        elif os.path.isdir(directory + "\\" + entry):
            Recurse(directory+"\\"+entry,jpgdirectory)

def makeImagePDF(imagepaths,pdfpath):
    #here we append the images
    firstimage = Image.open(imagepaths[0])
    firstimage.save(pdfpath, "PDF" ,resolution=100.0)
    batchsize = 10
    for i in range(1, len(imagepaths), batchsize):
    #for imagepath in imagepaths[1:]:
        end = min(len(imagepaths),i+batchsize)
        images = []
        for imagepath in imagepaths[i:end]:
            images.append(Image.open(imagepath))
        images[0].save(pdfpath,"PDF",resolution=100.0,save_all=True,
                       append=True,append_images=images[1:])


def makeToCPDF(pdftxtdirectory,titles,dates,pagecounts):
    width,height = letter
    toc_canvas = canvas.Canvas(pdftxtdirectory+"\\TableOfContents.pdf")
    toc_canvas.setFont('Helvetica', 20)
    tocy = height-inch
    x = 0+inch
    toc_canvas.drawCentredString(width/2, tocy,"Table of Contents")
    tocy = tocy-16*1.2

    toc_canvas.setFont('Helvetica', 14)
    for li in pdftxtdirectory.split('\\')[1:]:
        toc_canvas.drawCentredString(width/2, tocy,li)
        tocy = tocy-14*1.2
    tocy = tocy-14*1.2
    for title,date,pagecount in zip(titles,dates,pagecounts):
        if len(title) >= 32:
            title = title[:32]
        if len(date) >= 32:
            date = date[:32]
        if tocy <= inch:
            #we are at the bottom, go to the next page
            toc_canvas.showPage()
            toc_canvas.setFont('Helvetica', 14)
            tocy = height-inch
        toc_canvas.drawString(x,tocy,date + " | " + title)
        toc_canvas.drawString(width-inch,tocy,str(pagecount))
        tocy = tocy-12*1.2
    
    toc_canvas.showPage()
    toc_canvas.save()


def makePDF(pdftxtdirectory,jpgdirectory):
    #here we read in PDFtxt
    #we make table of contents, each titlepage, and the image compilations
    #then we append them all together
    width,height = letter
    x = 0+inch
    pagecounter = 1
    pdftxt = open(pdftxtdirectory+"\\PDFtxt.txt",'r')
    title_canvas = []
    titles = []
    dates = []
    pagecounts = []
    imagebools = []
    for line in pdftxt:
        #print(line)
        if line.startswith('#'):
            #this is a header
            if "Title:" in line:
                #this is the start of a new entry.
                #wrap up last entry.
                if title_canvas:
                    title_canvas.showPage()
                    title_canvas.save()
                    #append canvas to PDF

                    imagepdfpath = pdftxtdirectory + "\\" + title + " images.pdf"
                    if imagepaths:
                        makeImagePDF(imagepaths,imagepdfpath)
                        imagebools.append(True)
                    else:
                        imagebools.append(False)
                #open new PDF
                pagecounter += 1
                pagecounts.append(pagecounter)
                imagepaths = []
                title = next(pdftxt).rstrip()
                title = re.sub(r'[<>:"/\\|?*]', '', unidecode.unidecode(title))
                longtitle = title
                if len(title) >= 64:
                    title = title[:64]
                #check here if we missed a date
                if len(titles) > len(dates):
                    dates.append("Unlisted date")
                titles.append(title)
                title_canvas = canvas.Canvas(pdftxtdirectory+"\\"+title+".pdf")
                title_canvas.setFont('Helvetica', 12)
                titley = height-inch
                title_canvas.drawString(x,titley,line[1:].rstrip())
                titley = titley-12*1.2
                #need to text wrap the title
                i = 0
                while len(longtitle[i:]) > 72:
                    title_canvas.drawString(x,titley,longtitle[i:i+72])
                    titley = titley-12*1.2
                    i += 72
                title_canvas.drawString(x,titley,longtitle[i:])
                titley = titley-12*2               
            else:
                title_canvas.setFont('Helvetica', 12)
                title_canvas.drawString(x,titley,line[1:].rstrip())
                titley = titley-12*1.2
                if "Date" in line:
                    date = next(pdftxt).rstrip()
                    dates.append(date)
                    title_canvas.setFont('Helvetica', 12)
                    title_canvas.drawString(x,titley,date)
                    titley = titley-12*1.2
            #write this heading to the canvas
            
        elif line.startswith('!'):
            #this is an image
            imagepaths.append(jpgdirectory+"\\"+line[1:].rstrip())
            pagecounter += 1
        else:
            #this is a response to a heading
            #write this text to the canvas
            title_canvas.setFont('Helvetica', 12)
            resp = line.rstrip()
            i = 0
            while len(resp[i:]) > 72:
                title_canvas.drawString(x,titley,resp[i:i+72])
                titley = titley-12*1.2
                i += 72
            title_canvas.drawString(x,titley,resp[i:])
            titley = titley-12*2

    #close everything up
    title_canvas.showPage()
    title_canvas.save()
    #append canvas to PDF

    imagepdfpath = pdftxtdirectory + "\\" + title + " images.pdf"
    if imagepaths and len(imagepaths) < 1000:
        makeImagePDF(imagepaths,imagepdfpath)
        imagebools.append(True)
    else:
        imagebools.append(False)

    #now make the table of contents
    #check here if we missed a date
    if len(titles) > len(dates):
        dates.append("Unlisted date")
    #print(titles)
    #print(dates)
    #print(pagecounts)
    makeToCPDF(pdftxtdirectory,titles,dates,pagecounts)
    
    #here we will append all the PDFs
    merger = PdfFileMerger()

    merger.append(pdftxtdirectory+"\\TableOfContents.pdf")

    for title,boole in zip(titles,imagebools):
        with open(pdftxtdirectory+"\\"+title+".pdf", "rb") as f:
            merger.append(PdfFileReader(f))
        if boole:
            with open(pdftxtdirectory+"\\"+title+" images.pdf", "rb") as f:
                merger.append(PdfFileReader(f))

    directoryname = re.sub(r'[<>:"/\\|?*]', '',
                           unidecode.unidecode(pdftxtdirectory.split('\\')[-1]))
    merger.write(pdftxtdirectory+"\\"+directoryname+".pdf")
    print("Created {0}.pdf with {1} pages.".format(directoryname,pagecounter))
    merger.close()

    #now we need to delete the old files:
    for title,boole in zip(titles,imagebools):
        #print("Removing: " + title)
        try:
            os.remove(pdftxtdirectory+"\\"+title+".pdf")
        except FileNotFoundError:
            continue
        if boole:
            try:
                os.remove(pdftxtdirectory+"\\"+title+" images.pdf")
            except FileNotFoundError:
                continue
    

#default is 1000, but then PDFs longer than 1000 pages
#sys.setrecursionlimit(10000)
path = "E:\PARES\Archivo Historico de la Nobleza"
#path = "E:\PARES\Archivo General de Indias"
#path = "E:\PARES\Archivo General de Simancas"
#path = "E:\PARES\Archivo Historico Nacional"
jpgdirectory = "E:\PARES\jpgs"
Recurse(path,jpgdirectory)
