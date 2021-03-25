import sys
import urllib.request
import requests
import time
from bs4 import BeautifulSoup
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
from datetime import datetime
import re




class Page(QWebEnginePage):
    def __init__(self, url):
        self.app = QApplication(sys.argv)
        QWebEnginePage.__init__(self)
        self.html = ""
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl(url))
        self.app.exec_()

    def _on_load_finished(self):
        self.html = self.toHtml(self.Callable)

    def Callable(self, html_str):
        self.html = html_str
        self.app.quit()
        
        
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
    


def get_tracking(order_info):

    tracking_num = order_info["tracking_num"]
    order_info["last_tracking_date"] = None

    patterns = {"(delivery|has been delivered|was delivered|boîte à lettres du destinataire)":"delivered",
            "(arriv.+ dans le site en vue de sa distribution|delivery site)":"in_local_center",
            "(arriv.+ en france|roissy|paris)":"in_dest_country",
            "(quitt.+ son pays d'expédition|départ imminent du pays d'expédition|airline transit)":"in_airline",
            "(sorting center|sort facility|centre de tri)":"shipped"}
            
    try:
        days_remaining, events = get_tracking_by_scraping(tracking_num)
    except:
        days_remaining, events = [], []
    if days_remaining != []:
        order_info["time"] = days_remaining[0] + 1
    if events != []:
        if days_remaining == []:
            order_info["status"] = "delivered"
            order_info["last_tracking_date"] = events[0][0]
            return order_info
            
        for pattern in patterns.keys():
            for event in events:
                event_content = event[1]
                match = re.search(pattern,event_content.lower())
                if match:
                    order_info["status"] = patterns[pattern]
                    order_info["last_tracking_date"] = event[0]
                    return order_info
        return order_info
    
    if days_remaining == [] and events == []:
        print("error on scraping")
        headers = {"X-RapidAPI-Host":"apidojo-17track-v1.p.rapidapi.com","X-RapidAPI-Key":"9422eecb00msh60cc03d746d77adp122314jsn734330ae1c51"}
        k = 0
        try:
            while k < 2:
                r = requests.get("https://apidojo-17track-v1.p.rapidapi.com/track?codes={}".format(tracking_num),headers=headers)
                j = r.json()["dat"][0]["track"]
                if j != None:
                    if j["z0"] != "null":
                        lst = j["z1"]
                        break2 = False
                        for pattern in patterns.keys():
                            for event in lst:
                                match1 = re.search(pattern,event["z"].lower())
                                match2 = re.search(pattern,event["c"].lower())
                                if match1 or match2:
                                    order_info["status"] = patterns[pattern]
                                    order_info["last_tracking_date"] = shopify_date(event["a"])
                                    return order_info
                                    
                if order_info["status"] == "fulfilled":
                    k += 1
                    print("retrying 17track...")
                    time.sleep(10)
                else:
                    k = 2
        except:
            print("error on 17track")

    return order_info
    

def get_time(order_info):
    now = datetime.now()
    delta0 = now - order_info["date"]
    order_time = int(delta0.days)
    times = {"not_fulfilled":100,"fulfilled":20,"shipped":18,"in_airline":12,"in_dest_country":6,"in_local_center":3,"delivered":0}
    status = order_info["status"]
    if order_info["last_tracking_date"] != None:
        delta = now - order_info["last_tracking_date"]
    elif status != "not_fulfilled":
        delta = now - order_info["fulfillment_date"]
    else:
        delta = now - order_info["date"]
    if "time" not in order_info.keys():
        time = times[status] - delta.days
    else:
        time = order_info["time"]
    return time, order_time
    
    
    
    

order_info = {'order_id': '1956561059925', 'customer_id': '2797384728661', 'date': datetime(2019, 12, 7, 0, 0), 'name': '#2381', 'total_price': '39.90', 'status': 'fulfilled', 'fulfillment_date': datetime(2019, 12, 14, 0, 0), 'tracking_num': 'LO632311615CN'}
order_info = get_tracking(order_info)
order_info["time"], order_info["order_time"] = get_time(order_info)
print("better order infos detected :\n" + str(order_info))



