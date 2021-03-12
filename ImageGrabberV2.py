
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import os
import time

def click_and_write(lis,driver,o):
    o.write("#{0}\n".format(lis.string))
    #print(lis)
    vollink = driver.find_element_by_id(lis['id'])
    vollink.click()

    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.presence_of_element_located((By.ID, "imageGroup")))

    soup_level2=BeautifulSoup(driver.page_source,features="html.parser")
    hidden_images = soup_level2.find_all(value=re.compile("^http*"))
    print(len(hidden_images))
    for hi in hidden_images:
        o.write("{0}\n".format(hi['value']))
    return

#launch url
url = "http://go.galegroup.com.proxy.library.emory.edu/mss/start.do?p=SPOL&u=emory&authCount=1"


driver = webdriver.Chrome()
driver.implicitly_wait(30)
driver.get(url)


python_button = driver.find_element_by_id('login_button')
python_button.click()

username = driver.find_element_by_id("username")
password = driver.find_element_by_id("password")

username.send_keys("mhnicho")
password.send_keys("NyanPudgeEmailPa55")

python_button = driver.find_element_by_id('loginbutton')
python_button.click() 

linkByText = driver.find_element_by_link_text("Browse")
linkByText.click()

#Selenium hands the page source to Beautiful Soup
soup_level1=BeautifulSoup(driver.page_source,features="html.parser")

#now we are where we want to be

f = open("/Users/5cent/Downloads/State_Papers_Download_Set.txt",'r')

f.readline()


o = open("/Users/5cent/Desktop/State_Papers_URLs.txt",'w')

for line in f:
    name,remainder = line.split('/')
    t = soup_level1.find(string=re.compile(name))
    o.write(">{0}\n".format(t.rstrip()))
    p = t.parent
    plus = p.previous_sibling.find(href=re.compile("expand"))
    number = int(plus['id'][1:])
    expand = driver.find_element_by_id(plus['id'])
    expand.click()

    panel = soup_level1.find(id="title"+str(number))


    segments = remainder.split(';')
    for s in segments:
        spl = s.rstrip().split(':')
        #print(panel)
        start = spl[0]
        startstr = "Vol. {0} ".format(start)

        lis = panel.find("a",string=re.compile("Vol\.? {0} ".format(start)))
        if lis is None:
            print("no beuno")
            print(name)
            continue
        print(lis.string)
        click_and_write(lis,driver,o)
        if len(spl) == 1:
            continue
        end = spl[1] #inclusive
        endstr = "Vol. {0} ".format(end)
        endstr2 = "Vol {0} ".format(end)
        while True:
            lis = lis.next_element.next_element.next_element
            if lis is None:
                print("no beuno")
                print(name)
                continue
            click_and_write(lis,driver,o)
            #print(endstr)
            print(lis.string)
            if endstr in lis.string or endstr2 in lis.string:
                break

        #here we iterate over a numerical range,
        #instead we need to follow the page order
        #so we get next sibling while id != end
        """
        for v in range(int(spl[0]),int(spl[1])+1):
            print(v)
            lis =  panel.find("a",string=re.compile("Vol\. {0} ".format(v)))
            if lis is None:
                continue
            o.write("#{0}\n".format(lis.string))
            vollink = driver.find_element_by_id(lis['id'])
            vollink.click()

            wait = WebDriverWait(driver, 10)
            element = wait.until(EC.presence_of_element_located((By.ID, "imageGroup")))

            soup_level2=BeautifulSoup(driver.page_source,features="html.parser")
            hidden_images = soup_level2.find_all(value=re.compile("^http*"))
            print(len(hidden_images))
            for hi in hidden_images:
                o.write("{0}\n".format(hi['value']))

        """
o.close()
