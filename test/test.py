import re
import os
import sys
import shutil
import time
import random
import string
import codecs
import html
import json
import base64
import requests
import urllib.request
import apiai
import fbchat
from unidecode import unidecode
from datetime import datetime
from fbchat import Client, models
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl

Qapp = QApplication(sys.argv)


class Page(QWebEnginePage):
    global Qapp
    def __init__(self, url):
        self.app = Qapp
        QWebEnginePage.__init__(self)
        self.html = ""
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl(url))
        self.app.exec_()

    def _on_load_finished(self):
        k = 0
        while k < 25:
            time.sleep(2)
            h = self.toHtml(self.Callable)
            if h != None:
                break
            else:
                k+= 1
                    
        self.html = self.toHtml(self.Callable)

    def Callable(self, html_str):
        self.html = html_str
        self.app.quit()

"""
class Page(QWebEnginePage):
    global Qapp
    def __init__(self, url):
        self.app = Qapp
        QWebEnginePage.__init__(self)
        self.html = ""
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl(url))
        self.app.exec_()

    def _on_load_finished(self):
        k = 0
        while k < 25:
            
            time.sleep(2)
            h = self.toHtml(self.Callable)
            print(h)
            try:
                soup = BeautifulSoup(h, "html.parser")
                event_class = soup.find("div", class_="row parcel")
                if event_class != None:
                    event_lst = event_class.div.ul.findAll("li")
                    break
            except:
                k+= 1
                    
        self.html = self.toHtml(self.Callable)

    def Callable(self, html_str):
        self.html = html_str
        self.app.quit()
"""
"""
        
class Page(QWebEnginePage):
    global Qapp
    def __init__(self, url):
        self.app = Qapp
        QWebEnginePage.__init__(self)
        self.html = ""
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl(url))
        self.app.exec_()

    def _on_load_finished(self):
        time.sleep(2)
        self.html = self.toHtml(self.Callable)

    def Callable(self, html_str):
        self.html = html_str
        self.app.quit()
"""
        
def get_tracking_by_scraping(tracking_num):

    months = {"Jan":1, "Fév":2, "Mar":3, "Avr":4, "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Déc":12}

    URL = "http://parcelsapp.com/en/tracking/{}".format(tracking_num)
    page = Page(URL)
    soup = BeautifulSoup(page.html, "html.parser")

    days_remaining = []
    date_class = soup.find("div", class_="eta")
    if date_class != None:
        date_text = date_class.find("div", class_="text")
        if date_text != None:
            date = date_text.p.text.strip()
            match = re.search(r",\s(\d{1,2}\s-\s\d{1,2})", date)
            if match:
                lst = match.group(1).split(" - ")
                days_remaining = [int(lst[0]), int(lst[1])]
            
    events = []
    event_class = soup.find("div", class_="row parcel")
    if event_class != None:
        event_lst = event_class.div.ul.findAll("li")
        if event_lst != []:
            for event in event_lst:
                time, content = None, None
                event_time = event.find("div", class_="event-time")
                event_content = event.find("div", class_="event-content")
                if event_time != None:
                    time_text = event_time.strong.text
                    lst = time_text.split(" ")
                    for month in months.keys():
                        if lst[1] == month:
                            lst[1] = months[month]
                            time = datetime(int(lst[2]),lst[1],int(lst[0]))
                            break
                            
                if event_content != None:
                    content = event_content.strong.text
                events.append([time,content])
                    
    return days_remaining, events
    

tracking_num_1 = "LO849049765CN"
tracking_num_2 = "LO849039755CN"

days_remaining, events = get_tracking_by_scraping(tracking_num_1)
days_remaining, events = get_tracking_by_scraping(tracking_num_2)
print(days_remaining)
print(events)



