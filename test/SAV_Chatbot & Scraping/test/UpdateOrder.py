import base64
import codecs

import requests
import urllib.request
import apiai
import fbchat
from datetime import datetime
from fbchat import Client, models
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl

from Apiai_reqTest import Shopîfy


class Shopîfy(object):
    pass


def get_first_order_id(api_key, shop):
    pass


def shopify_request(shop, param, param1, param2):
    pass


class QuestionTest(Shopîfy):
    def update_order_ids(shop, shopify_api_url=None):
    
        file = open("shops/{}/order_ids.csv".format(shop) ,"r")
        init = file.read()
        file.close()
        new = ""
        if len(init) > 5:
            lst = init.split("\n")
            last_id = lst[len(lst ) -1].split(",")[1]
            new = "\n"
        else:
            api_key = shopify_api_url[shop]
            first_order_id = get_first_order_id(api_key, shop)
            last_id = first_order_id
        k = ""
        while k != "stop":
            r = shopify_request(shop ,"get" ,"orders.json"
                                ,"?since_id={}&status=any&limit=250&fields=id,name".format(last_id))
            j = r.json()
            n_orders = len(j["orders"])
            if n_orders == 0:
                return last_id
            for i in range(n_orders):
                order_id = j["orders"][i]["id"]
                order_name = j["orders"][i]["name"].replace("#" ,"")
                new += "{},{}\n".format(order_name ,order_id)
                if i == n_orders - 1:
                    last_id = order_id
                    if i != 249:
                        k = "stop"
            print("Updating order ids...")
        file2 = open("shops/{}/order_ids.csv".format(shop) ,"w")
        file2.write("{}{}".format(init ,new[:len(new ) -1]))
        file2.close()
        return last_id