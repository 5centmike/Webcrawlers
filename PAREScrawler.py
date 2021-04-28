
from seleniumwire import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import re
import os
import time
from PIL import Image
import requests
from io import BytesIO
import time
import re
import unidecode
import unidecode


#Create our own file system to mimic the tree

#Recursive algorithm to traverse entire tree.
#For each parent ID we create a directory.
#We just need to grab all children IDs from 'contiene'
#Then from nodes we can grab metadata and descriptions from 'description'
#Then we grab images from 'show'

class Tree:
    def __init__(self, name):
        self.children = []
        self.name = name

    def __str__(self, level=0):
        ret = "\t"*level+repr(self.name)+"\n"
        for child in self.children:
            ret += child.__str__(level+1)
        return ret


def ScrapeMeta(soup):
    info = []
    for div in soup.find_all("div"):
        if div.has_attr("class"):
            if div["class"] == ["info"]:
                info.append(div)

    meta = {}
    for i in info:
        h4 = i.find("h4")
        p = i.find("p")
        if h4 and p:
            #print(h4)
            #print(p)
            #meta[h4.string] = ' '.join(next(p.stripped_strings).split())
            meta[h4.string.rstrip()] = ' '.join(p.get_text().split())
    return meta

def CheckYear(string,startyear,endyear):
    yearstring =  "\d{4}"
    yearre = re.compile(yearstring)
    matches = re.findall(yearre,string)
    for match in matches:
        year = int(match)
        if year >= startyear and year <= endyear:
            return True
    if len(matches)==2:
        s = int(matches[0])
        e = int(matches[1])
        if s <= startyear and e >= endyear:
            return True
    
    return False


class CheckAttributeValue(object):
    def __init__(self, locator, attribute, value):
        self.locator = locator
        self.attribute = attribute
        self.value = value

    def __call__(self, driver):
        try:
            element_attribute = EC._find_element(driver, self.locator).get_attribute(self.attribute)
            return element_attribute == self.value
        except StaleElementReferenceException:
            return False


def Recurse(id_num,directory,driver,url,startyear,endyear,tree,completedids,idfile):
    #first get description
    driver.get(url+"description/"+id_num)
    #Selenium hands the page source to Beautiful Soup
    soup=BeautifulSoup(driver.page_source,features="html.parser")
    meta = ScrapeMeta(soup)
    try:
        directory_name = directory + "/" +re.sub(r'[<>:"/\\|?*]', '', unidecode.unidecode(meta['Formal Title:']))
    except KeyError:
        if 'Reference number:' in meta:
            directory_name = directory + "/" +re.sub(r'[<>:"/\\|?*]', '', unidecode.unidecode(meta['Supplied Title:']+" "+meta['Reference number:']))
        else:
            directory_name = directory + "/" +re.sub(r'[<>:"/\\|?*]', '', unidecode.unidecode(meta['Supplied Title:']))

    #check if directory exists and if  not make it
    if not os.path.exists(directory_name):
              print("Making directory: {0}".format(directory_name))
              os.mkdir(directory_name)
    #now make text file containing the metadata of this directory
    o = open(directory_name+"/Metadata.txt",'w')
    for k,v in meta.items():
        o.write(k+"\n")
        o.write(v+"\n")
    o.close()


    #check if this entry has any contents:
    if not "Contains:" in meta:
        #this entry has no contents so continue
        return
    
    #now go into the listed contents of this node and
    #make a list of new ids to either recurse into or to compile into PDFs
    driver.get(url+"contiene/"+id_num)

    #here, sort by date
    select = Select(driver.find_element_by_id('orderBy'))
    select.select_by_visible_text('Date')
    wait = WebDriverWait(driver, 20)
    #wait here for table to be opaque again:
    wait.until(CheckAttributeValue((By.CLASS_NAME, "displayTable"), "style", "opacity: 1;"))
    soup=BeautifulSoup(driver.page_source,features="html.parser")
    
    #check if we are iterating over actual documents now
    penultimate = False
    imgs = soup.find_all("img")
    for img in imgs:
        if img['src'].startswith("/ParesBusquedas20/img/iconoNivel20.gif") or img['src'].startswith("/ParesBusquedas20/img/iconoNivel19.gif"):
            penultimate=True
            break
    
    #print(links)
    ids = []
    idtrees = []
    pagecount = 1
    more = True
    #initialize childnames
    childdic = {}
    for t in tree.children:
        childdic[t.name] = t
    childflag = False
    if childdic:
        childflag = True

    #placeholder
    maxpagenum = 1
    
    while pagecount <= maxpagenum:
        pagecount+=1
        #more = False
        links = soup.find_all("a")
        for a in links:
            if not a.has_attr('class') and a['href'].startswith("/ParesBusquedas20/catalogo/description/"):
                #here we find the date and check it and if outside range we skip.
                dates = a.parent.parent.find("p", class_="fecha")
                #if dates aren't listed include anyways
                if dates:
                    years = dates.get_text()
                    if not CheckYear(years,startyear,endyear):
                        continue
                #if childnames are empty don't worry about it
                if not childflag:
                    newid = a['href'].split('/')[-1]
                    if not newid in completedids:
                        ids.append(newid)
                        #here we need to append an empty tree
                        idtrees.append(Tree(newid))
                        #print("Appending: {0}".format(a['href'].split('/')[-1]))
                else:
                #now check here to see if this name is in our tree.
                    todel = []
                    for name in childdic.keys():
                        #print("Checking {0} in {1}:".format(name,a.string))
                        if name in a.string:
                            newid = a['href'].split('/')[-1]
                            if not newid in completedids:
                                ids.append(newid)
                                idtrees.append(childdic[name])
                                todel = name
                                #print("Found {0} in {1}".format(name,a.string))
                                #print("Appending: {0}".format(a['href'].split('/')[-1]))
                                continue
                        #if not childdic:
                        #    continue
                    if todel:
                        del childdic[todel]
                        if not childdic:
                            break
            #if a.has_attr('title')and a['title'] == "Go to page {0}".format(str(pagecount)):
            if a.string  == "»|":
                latterhalf = a['href'].split('-p=')[1]
                maxpagenum = int(latterhalf.split('&')[0])
                #print("maxpagenum set to {0}".format(maxpagenum))
            #find next page button with selenium and click it
        if pagecount <= maxpagenum:
            #print("But wait! There's more! Going to page {0}".format(pagecount))
            #nextpage = driver.find_element_by_link_text(str(pagecount))
            #print('nextpage')
            #print(nextpage)
            attempts = 0
            success = False
            while not success:
                try:
                    wait = WebDriverWait(driver, 20)
                    #check if this link really exists:
                    #try:
                    #    empty = driver.find_element(By.LINK_TEXT, str(pagecount))
                    #except NoSuchElementException:
                    #    print("No next page link found to page {0}.".format(str(pagecount)))
                    #    more = False
                    #    break
                                              
                    nextpage = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, str(pagecount))))
                    nextpage.click()
                except StaleElementReferenceException:
                    attempts += 1
                    if attempts > 10:
                        print("Tried to click 10 times!!")
                        break
                success = True
                
            wait = WebDriverWait(driver, 20)
            #wait here for table to be opaque again:
            wait.until(CheckAttributeValue((By.CLASS_NAME, "displayTable"), "style", "opacity: 1;"))
            time.sleep(1)
            soup=BeautifulSoup(driver.page_source,features="html.parser")

    if childdic:
        print("Missing children:")
        print(childdic.keys())
        m = open('Missing.txt','a')
        for k in childdic.keys():
            m.write(k + '\n')
        m.close()
        
    #print(ids)

    #determine if this is a penultimate or not
    #we determined this above by looking for thumbnails
    if penultimate:
        #this is penultimate
        #now we will make a PDF
        #iterate over every ID and add it to the PDF.
        #to make PDF we will download all the images and make a text file containing image IDs
        #and metadata
        pdftxt = open(directory_name+"/PDFtxt.txt",'w')
        
        for i in ids:
            digitized = False
            #first we get the metadata for every entry
            driver.get(url+"description/"+i)
            soup=BeautifulSoup(driver.page_source,features="html.parser")
            m = ScrapeMeta(soup)
            #print(m)
            #check here for date. If date outside range, just skip this entry.
            #year = int(m["Date of creation:"].split("-")[0])
            #if year <= startyear or year >= endyear:
                #we are not in range so skip this one.
                #continue
            if "Date of creation:" in m:         
                if not CheckYear(m["Date of creation:"],startyear,endyear):
                    #we are not in range so skip this one.
                    continue
                #we are in range
                #print("Year match: {0}".format(m["Date of creation:"]))
            for k,v in m.items():
                pdftxt.write("#"+k+"\n")
                pdftxt.write(v+"\n")

            #if there exists a view images button then the entry is digitized
            if soup.find(string="View Images"):
                    #print("Digitized!")
                    digitized=True                
            #links = soup.find_all("a")
            #for a in links:
            #if a.has_attr('href') and a['href'] == "/ParesBusquedas20/catalogo/show/{0}".format(str(i)):

        
            #if it's digitized we grab all the images and metadata and store them
            #else if it isn't digitized we get just the metadata and store that.
            if digitized:
                pdf_path = directory_name+".pdf"
                driver.get(url+"show/"+i)
                soup=BeautifulSoup(driver.page_source,features="html.parser")
                #now we need to get the total images count and then download each
                spans = soup.find_all("span")
                pagnum = 1
                for span in spans:
                    #print("checking spans")
                    if span.has_attr('class') and not span.has_attr('id'):
                        #print("Updating pagnum")
                        pagnum = int(span.string)
                        #print("we got a span here")
                        #print(span)
                        #print(span.string)
                        #if span['class'] == "numPag":
                #print(pagnum)
                #write pagnum to PDF
                pdftxt.write("#Number of pages:\n")
                pdftxt.write(str(pagnum)+"\n")
                #now we need to get dbcode for each image
                img = soup.find(style=re.compile("position: absolute; top:"))
                #print(img)
                split = img['src'].split('&')
                dbcode=0
                for s in split:
                    if s.startswith("dbCode="):
                        dbcode = s.split("=")[1]
                if not dbcode:
                    print("dbCode not set")
                if pagnum > 1000:
                    print("Skipping a really big file.")
                    continue
                for x in range(1,pagnum+1):
                    #TODO Figure out how to request this and save it appropriately
                    src = "http://pares.mcu.es/ParesBusquedas20/ViewImage.do?txt_id_imagen={0}&txt_zoom=10".format(str(x))
                    #here we download the image
                    driver.get(src)
                    last = driver.last_request
                    if not last.url == src:
                        #this is not what we are looking for
                        for request in driver.requests[-1:-3:-1]:
                            if request.url == src:
                                last = request
                                break
                    #if not last:
                    #    print("waiting")
                    #    last = driver.wait_for_request(src)
                    disposition = last.response.headers['Content-Disposition']
                    if not disposition:
                        print(
                            last.url,
                            last.response.status_code,)
                    jpgname = disposition.split('=')[-1]
                    #print(jpgname)
                    #we have saved an image. We need a txt document for each PDf we are making.
                    #it will contain the metadata and the image IDs.
                    #pdftxt.write("!{0}.jpg\n".format(int(dbcode)+x-1))
                    pdftxt.write("!{0}\n".format(jpgname))
                    
                
            else:
                #just write out the metadata for each item.
                #print("Undigitized!")
                continue
                
                                                                    
            #min #THIS WORKS
            #http://pares.mcu.es/ParesBusquedas20/ViewImage.do?txt_id_imagen=1&dbCode=34090938&txt_zoom=10
            #http://pares.mcu.es/ParesBusquedas20/ViewImage.do?txt_id_imagen=1&txt_zoom=10
        pdftxt.close()
    else:
        #if not penultimate, recurse
        for i,t in zip(ids,idtrees):
            Recurse(i,directory_name,driver,url,startyear,endyear,t,completedids,idfile)

    idfile.write(str(id_num)+"\n")
    idfile.flush()
    print("Writing completed ID {0}".format(str(id_num)))

#driver = webdriver.Chrome()
#driver.implicitly_wait(30)
path = os.path.dirname('E:\PARES\jpgs\poop')
print(path)
print(path + os.path.sep)

preferences = {
                "profile.default_content_settings.popups": 0,
                "download.default_directory": path + os.path.sep,
                "directory_upgrade": True
            }
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option('prefs', preferences)
driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(10) # seconds

#chrome_options = webdriver.ChromeOptions()
#prefs = {'download.default_directory' : 'D:/PARES/jpgs//'}
#prefs = {'download.default_directory' : 'C:/Users/5cent/Desktop/jpgs'}
#chrome_options.add_experimental_option('prefs', prefs)
#driver = webdriver.Chrome(options=chrome_options)


#id_num = "3907727"
#id_num = "3913217"
#directory = "D:/PARES/"
directory = "E:/PARES/"
url = "http://pares.mcu.es/ParesBusquedas20/catalogo/"
startyear = 1700
endyear = 1716

#here we read in Tree.txt and parse it to create our own tree in memory.
#Then we run Recurse and pass it the tree. When Recurse is passed an empty tree it takes everything.
treefile = open(directory+"Tree.txt",'r',encoding='utf8')
treehash = {}
for line in treefile:
    li = line.split()
    pos = li[0]
    name = " ".join(li[1:])
    if pos.count('.') == 1:
        #this is a new tree
        treehash[pos[0]] = Tree(name)
    else:
        #find the right subtree
        tree = treehash[pos[0]]
        for i in pos.split('.')[1:-2]:
            #print(pos)
            #print(i)
            tree = tree.children[int(i)-1]
        tree.children.append(Tree(name))

#t = treehash['2']
#print(t)

#here we want a file containing all of the ids that we have already exhausted.
#Then we check that list when adding IDs.

idfile = open(directory+"CompletedIDs.txt",'r')
completedids = set()
for line in idfile:
    completedids.add(line.strip())

idfile.close()
print("Skipping {0} IDs".format(len(completedids)))

idfile = open(directory+"CompletedIDs.txt",'a')


idnames = {"Archivo General de Indias":'10',"Archivo Histórico de la Nobleza":'3',
           "Archivo Histórico Nacional":'9',"Archivo General de Simancas":'2'}

for i,tree in treehash.items():
    id_num = idnames[tree.name]
    Recurse(id_num,directory,driver,url,startyear,endyear,tree,completedids,idfile)
    print("DONE WITH {0}".format(tree.name))


idfile.close()
#daterange  01/01/1700 -> 12/31/1716


