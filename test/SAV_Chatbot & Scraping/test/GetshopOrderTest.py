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


def build_clients_dic():
    pass


class QuestionTest(Shopîfy):
    def get_first_order_id(api_key, shop):
        print("Première synchronisation avec le shop {}, initialisation en cours...".format(shop))
        date = str(datetime.now())[:10]
        date += "T01:00:00-01:00"
        while True:
            print(date)
            r = requests.get("{}/orders.json?created_at_max={}&status=any&limit=250".format(api_key, date))
            lst = r.json()["orders"]
            if len(lst) == 250:
                date = lst[249]["created_at"]
            else:
                order_id = lst[len(lst) - 1]["id"]
                return order_id


    def shop_dic(self):
        file = open("credentials.csv", "r")
        cont = file.read()
        file.close()
        lst2, shops = [], []
        shopify_api_url, client_id, client_secret, refresh_token, user_id, api_key, sav_mail, img = {}, {}, {}, {}, {}, {}, {}, {}
        lst = cont.split("\n")
        for i in range(len(lst)):
            lst2.append(lst[i].split(","))
        for k in range(1, len(lst2)):
            shop = lst2[k][0]
            shopify_api_url[shop] = lst2[k][1]
            client_id[shop] = lst2[k][2]
            client_secret[shop] = lst2[k][3]
            refresh_token[shop] = lst2[k][4]
            user_id[shop] = lst2[k][5]
            api_key[shop] = lst2[k][6]
            sav_mail[shop] = lst2[k][7]
            img[shop] = lst2[k][8]
        for key in shopify_api_url.keys():
            shops.append(key)
        return shops, shopify_api_url, client_id, client_secret, refresh_token, user_id, api_key, sav_mail, img


    def build_clients_dic(self):
        file = open("clients.csv", "r")
        cont = file.read()
        file.close()
        lst = cont.split("\n")
        lst2 = []
        for i in range(len(lst)):
            lst2.append(lst[i].split(","))
        dic = {}
        for client in lst2:
            shops = client[1].split(";")
            fb_thread_id = client[2]
            today_msg = int(client[3])
            today_nt = int(client[4])
            credit = int(client[5])
            dic[client[0]] = {"shops": shops, "thread_id": fb_thread_id, "today_msg": today_msg, "today_nt": today_nt,
                              "credit": credit}
        return dic


    def update_clients_dic(clients, owner, today_msg, today_nt, credit):
        for client in clients:
            if client == owner:
                clients[client]["today_msg"] = str(today_msg)
                clients[client]["today_nt"] = str(today_nt)
                clients[client]["credit"] = str(credit)
                break

        cont4 = ""
        for a in clients.keys():
            cont4 += "{},{},{}\n".format(a, ";".join(clients[a]["shops"]),
                                         ",".join(list([str(b) for b in clients[a].values()])[1:]))

        file = open("clients.csv", "w")
        file.write(cont4[:-1])
        file.close()


    def reset_clients_dic(self):
        clients = build_clients_dic()
        for client in clients.keys():
            clients[client]["today_msg"] = "0"
            clients[client]["today_nt"] = "0"

        cont4 = ""
        for a in clients.keys():
            cont4 += "{},{},{}\n".format(a, ";".join(clients[a]["shops"]),
                                         ",".join(list([str(b) for b in clients[a].values()])[1:]))
        file = open("clients.csv", "w")
        file.write(cont4[:-1])
        file.close()


    def token_dic(shops):
        access_tokens = {}
        for i in shops:
            access_tokens[i] = "init"
        return access_tokens


    def build_messages_dic(shops):
        messages_dic_1, messages_dic_2 = {}, {}
        for n in range(1, 3):
            for shop in shops:
                file = codecs.open("shops/{}/messages_dic_{}.csv".format(shop, n), encoding="utf-8")
                cont = file.read()
                file.close()
                lst = cont.split("\n")[2:]
                lst2, lst3, lst4 = [], [], []
                for i in range(len(lst)):
                    lst2.append(lst[i].split(","))
                for j in range(len(lst2)):
                    for k in range(len(lst2[j])):
                        lst2[j][k] = lst2[j][k].split(" ; ")
                if n == 1:
                    messages_dic_1[shop] = lst2
                elif n == 2:
                    messages_dic_2[shop] = lst2
        return messages_dic_1, messages_dic_2


    def build_history(shop):
        history = []
        file = open("shops/{}/history.csv".format(shop), "r")
        cont = file.read()
        file.close()
        lst = cont.split("\n")
        for i in range(len(lst) - 1, -1, -1):
            history.append(lst[i].split(","))
        return history

