import base64
import codecs
from pydoc import html
from typing import re

import requests
import urllib.request
import apiai
import fbchat
from datetime import datetime, time
from fbchat import Client, models
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl

from Apiai_reqTest import Shopîfy
from GetCustomer import shopify_date

### CLass WebEnginePage
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
            time.sleep(15)
            self.html = self.toHtml(self.Callable)

        def Callable(self, html_str):
            self.html = html_str
            self.app.quit()


    def get_tracking_by_scraping(tracking_num):

        months = {"Jan" :1, "Fév" :2, "Mar" :3, "Avr" :4, "May" :5, "Jun" :6, "Jul" :7, "Aug" :8, "Sep" :9, "Oct" :10, "Nov" :11, "Déc" :12}

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
                                time = datetime(int(lst[2]) ,lst[1] ,int(lst[0]))
                                break

                    if event_content != None:
                        content = event_content.strong.text
                    events.append([time ,content])

        return days_remaining, events


    def get_tracking(order_info):

        tracking_num = order_info["tracking_num"]
        order_info["last_tracking_date"] = None

        patterns = {"(delivery|has been delivered|was delivered|boîte à lettres du destinataire)" :"delivered",
                    "(arriv.+ dans le site en vue de sa distribution|delivery site)" :"in_local_center",
                    "(arriv.+ en france|roissy|paris)" :"in_dest_country",
                    "(quitt.+ son pays d'expédition|départ imminent du pays d'expédition|airline transit)" :"in_airline",
                    "(sorting center|sort facility|centre de tri)" :"shipped"}

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
                    match = re.search(pattern ,event_content.lower())
                    if match:
                        order_info["status"] = patterns[pattern]
                        order_info["last_tracking_date"] = event[0]
                        return order_info
            return order_info

        if days_remaining == [] and events == []:
            print("error on scraping")
            headers = {"X-RapidAPI-Host" :"apidojo-17track-v1.p.rapidapi.com"
                       ,"X-RapidAPI-Key" :"9422eecb00msh60cc03d746d77adp122314jsn734330ae1c51"}
            k = 0
            try:
                while k < 2:
                    r = requests.get("https://apidojo-17track-v1.p.rapidapi.com/track?codes={}".format(tracking_num)
                                     ,headers=headers, timeout=15)
                    j = r.json()["dat"][0]["track"]
                    if j != None:
                        if j["z0"] != "null":
                            lst = j["z1"]
                            break2 = False
                            for pattern in patterns.keys():
                                for event in lst:
                                    match1 = re.search(pattern ,event["z"].lower())
                                    match2 = re.search(pattern ,event["c"].lower())
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
        times = {"not_fulfilled" :100 ,"fulfilled" :20 ,"shipped" :18 ,"in_airline" :12 ,"in_dest_country" :6
                 ,"in_local_center" :3 ,"delivered" :0}
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

    ###########################################################

    def body_decoder(body):
        b64_char  = base64.urlsafe_b64decode(body)
        utf8_char = b64_char.decode("utf-8")
        html_char = html.unescape(utf8_char)
        html_char = html_char.replace("\r\n" ,"\n").replace("\n" ,".")
        pattern1 = r"(Le|On).{15,30}:\d{2}.+"
        pattern2 = r"(Le|On).{20,120}(a écrit|wrote).+"
        pattern3 = r"\-{10}.Forwarded.message.+"
        pattern4 = r"(De|Da|From)\s?:.+"
        pattern5 = r"Provenance :.+"
        pattern6 = r"Inviato da Posta.+"
        pattern7 = r"Message du.{5,20}:\d{2}.+"
        pattern8 = r"envoyé :.{20,300}de :.+"
        pattern9 = r"Merci pour votre achat !.+"
        for pattern in [pattern1 ,pattern2 ,pattern3 ,pattern4 ,pattern5 ,pattern6 ,pattern7 ,pattern8 ,pattern9]:
            html_char = re.sub(pattern, "", html_char)
        if len(html_char) > 1000:
            return "too_long"
        pattern_html = r"\</*[^\>]*\>"
        decoded_body = re.sub(pattern_html, "", html_char)
        decoded_body = decoded_body.replace(u'\xa0', ' ')
        while "  " in decoded_body or ".." in decoded_body:
            decoded_body = decoded_body.replace("  " ," ").replace(".." ,".")
        return decoded_body


def gmail_request(shop, param, param1):
    pass


def gmail_get_message(shop, msg_id, name_list=None):
        message = {}
        r = gmail_request(shop ,"get" ,"messages/{}".format(msg_id))
        j = r.json()
        if "STARRED" in j["labelIds"]:
            return {"STARRED"}
        message["threadId"] = j["threadId"]
        lst1 = j["payload"]
        lst2 = lst1["headers"]
        for dic in lst2:
            if dic["name"].lower() == "message-id":
                message["Message_ID"] = dic["value"][1:-1]
            if dic["name"].lower() == "from":
                From = dic["value"]
            if dic["name"].lower() == "subject":
                message["subject"] = dic["value"]
            if "data" in lst1["body"]:
                Data = lst1["body"]["data"]
            else:
                for i in range(len(lst1["parts"])):
                    try:
                        if lst1["parts"][i]["body"]["data"] != "":
                            Data = lst1["parts"][i]["body"]["data"]
                            break
                    except:
                        for j in range(len(lst1["parts"][i]["parts"])):
                            if lst1["parts"][i]["parts"][j]["body"]["data"] != "":
                                Data = lst1["parts"][i]["parts"][j]["body"]["data"]
                        break

        pattern = r"\<([^\s@]+@[^\s\.]+\.[\S]+)\>"
        match = re.search(pattern ,From)
        if match:
            message["email"] = match.group(1)
        else:
            message["email"] = From

        data = body_decoder(Data)
        source_language, translation = deepl_front(data)
        message["source_language"] = source_language
        if source_language == "FR":
            message["data"] = data
        else:
            message["data"] = translation

        full_name = re.sub(pattern ,"" ,From)
        message["full_name"] = full_name
        lst = full_name.lower().split(" ")
        # try to get first name:
        message["first_name"] = ""
        for i in lst:
            if i in name_list:
                message["first_name"] = " " + i.capitalize().replace(" " ,"")
                break

        return message


    def detect_order_name(message):
        for text in [message["subject"] ,message["data"]]:
            order_name = "not found"
            match = re.search(r"\D(\d{4,5})\D" ,"{}{}{}".format("a" ,text ,"a"))
            if match:
                num = int(match.group(1))
                if num < 60000 and num > 1000:
                    order_name = str(num)
                    break
        return order_name


    def detect_irritation_score(message):
        lst1 = \
        ("arnaque", "escro", "voleur", "colere", "colère", "pas content", "mecontent", "mécontent", "honte", "inadmissible",
        "fureur", "furie", "fache", "fâche", "rage", "inacceptable", "inexcusable")
        lst2 = ("plainte", "justice", "judiciaire", "polic", "flic", "gendarmerie", "demeure", "avocat", "tribunal",
                "services compétents")
        text = message["data"]
        pattern_1 = r"[A-Z]{2,}";
        pattern_2 = r"(!|\?){2,}"
        s1 = len(re.findall(pattern_1, text)) - len(re.findall(r"(RE|COMMANDE|MERCI)", text))
        s2 = len(re.findall(pattern_2, text))
        s3 = 0
        for word in lst1 + lst2:
            s3 += len(re.findall(word, text.lower()))
        s4 = len(re.findall(r"!", text))
        score = round(((s1 + s2 * 2 + s3) ** (1 / 2)) * 30 + 10 * s4 ** (1 / 2))
        if score > 100:
            score = 100
        # MENACE DETECTION:
        menace = False
        for word in lst2:
            if re.search(word, text.lower()):
                menace = True

        return score, menace


    def deepl_front(text):
        error = True
        phrases = text.split(".")
        for phrase in phrases:
            if re.search(r"\w+\s\w+\s\w+", phrase):
                r = requests.post(
                    "https://api.deepl.com/v2/translate?auth_key=478283b2-3683-820d-9433-2d3c243eb689&target_lang=FR&text={}".format(
                        phrase), timeout=15)
                error = False
                break
        if not error:
            translations = r.json()["translations"]
        else:
            return "ERROR", None
        source_language = translations[0]["detected_source_language"]
        if source_language == "FR":
            return "FR", None
        else:
            r = requests.post(
                "https://api.deepl.com/v2/translate?auth_key=478283b2-3683-820d-9433-2d3c243eb689&target_lang=FR&text={}".format(
                    text), timeout=15)
            translations = r.json()["translations"]
            translation = translations[0]["text"]
            return source_language, translation


    def deepl_back(text, target_lang):
        tags = re.findall(r"<[^>]*>", text)
        lines = re.findall(r">([^<]*)<", text)

        phrases = ""
        for line in lines:
            phrases += "&text={}".format(line)

        r = requests.post(
            "https://api.deepl.com/v2/translate?auth_key=478283b2-3683-820d-9433-2d3c243eb689&target_lang={}{}".format(
                target_lang, phrases), timeout=15)
        translations = r.json()["translations"]
        translation_text = []
        for t in translations:
            translation_text.append(t["text"])
        len_t = len(tags)
        len_p = len(translation_text)
        new_text = ""
        for i in range(max(len_t, len_p)):
            if i <= len_t:
                new_text += tags[i]
            if i <= len_p:
                new_text += translation_text[i]

        return new_text


    def append_message_id(message_id):
        global lst_message_ids
        lst_message_ids.append(message_id)
        file = open("message_ids.csv", "a")
        file.write("\n{}".format(message_id))
        file.close()


    def put_a_star(shop, message):
        thread_id = message["threadId"]
        post_data = {"addLabelIds": ["STARRED"]}
        gmail_request(shop, "post", "threads/{}/modify".format(thread_id), post_data=post_data)
