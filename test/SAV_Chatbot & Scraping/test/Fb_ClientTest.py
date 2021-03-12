import base64
import codecs
import os
import shutil

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
from GetshopOrderTest import build_clients_dic
from ModifyAdressTest import create_mime_msg
from WebEnginePageTest import put_a_star, gmail_request, append_message_id, detect_irritation_score, detect_order_name, \
    get_tracking, get_time, gmail_get_message
from test.Gmail_ResquestTest import Shopify


def token_dic(shops):
    pass


def reset_clients_dic():
    pass


def build_messages_dic(shops):
    pass


def build_text_msg(shop, response, param, message, param1, history):
    pass


def detect_question(param, param1):
    pass


def shopify_get_customer(shop, message, history):
    pass


def shopify_get_orders(shop, message, customer_id):
    pass


def build_answer(shop, order_info, message, questions, history, is_buffalo):
    pass


def buffalo(shops, message, history):
    pass


def build_history(shop):
    pass


def shop_dic():
    pass


class QuestionTest(Shopify):



    # fb_client = fb_login()

    print("getting data...")

    shops ,shopify_api_url ,client_id ,client_secret ,refresh_token ,user_id ,api_key ,sav_mail ,img = shop_dic()
    clients = build_clients_dic()
    access_tokens = token_dic(shops)

    file = open("message_ids.csv" ,"r")
    cont_message_ids = file.read()
    file.close()
    lst_message_ids = cont_message_ids.split("\n")

    file = open("liste_prenom_FR_EN.txt" ,"r")
    cont2 = file.read()
    file.close()
    name_list = cont2.split("\n")

    file = open("zip_codes_FR.csv" ,"r")
    cont3 = file.read()
    file.close()
    lst = cont3.split("\n")
    lst_zip_codes = []
    for zip in lst:
        lst_zip_codes.append(zip.split(","))
    lst = []

    CANCEL_ID = "16"
    REFUND_ID = "999"
    ADDRESS_ID = "21"

    START = 20

    print("get data sucessful.\nWaiting for a new message")

    h = True

    while True:
        now = datetime.now()
        if now.hour == 1:
            h = True
        if now.hour == 0 and h:
            reset_clients_dic()
            h = False

        for shop in shops:
            is_buffalo = False
            if shop == "BUFFALO":
                is_buffalo = True
            # GMAIL:
            r = gmail_request(shop ,"get" ,"messages" ,endpoints="maxResults={}&q=label:inbox&".format(START))
            messages = r.json()["messages"]
            for message in messages:
                message_id = message["id"]
                if message_id not in lst_message_ids:

                    if is_buffalo:
                        shop = "BUFFALO"

                    for kjkj in "a":
                        # Update the files:
                        shops ,shopify_api_url ,client_id ,client_secret ,refresh_token ,user_id ,api_key ,sav_mail ,img = shop_dic()
                        for shop2 in shops:
                            if not os.path.exists("shops/{}".format(shop2)):
                                shutil.copytree("shops/__default__" ,"shops/{}".format(shop2))
                        clients = build_clients_dic()
                        messages_dic_1 ,messages_dic_2 = build_messages_dic(shops)
                        history = build_history(shop)

                        message = gmail_get_message(shop ,message_id)

                        if shop == "BUFFALO":
                            shop, customer_id = buffalo(shops, message, history)
                            if shop != None:
                                client_id[shop] = client_id["BUFFALO"]
                                client_secret[shop] = client_secret["BUFFALO"]
                                refresh_token[shop] = refresh_token["BUFFALO"]
                                user_id[shop] = user_id["BUFFALO"]
                                api_key[shop] = api_key["BUFFALO"]
                                sav_mail[shop] = sav_mail["BUFFALO"]
                                img[shop] = img["BUFFALO"]
                            else:
                                q = True
                                for l in history:
                                    if l[0] == message["email"]:
                                        q = False
                                        message_text = "I could not find info on this customer"
                                        put_a_star(shop, message)
                                        mime_msg = create_mime_msg(sav_mail["BUFFALO"], message_text, message)
                                        gmail_request("BUFFALO" ,"post" ,"drafts" ,endpoints="", post_data={"message" :mime_msg})
                                        break
                                if q:
                                    response = "Afin de pouvoir vous aider, pourriez vous poser cette question en répondant au mail de confirmation de commande que vous avez reçu au moment de l'achat."
                                    message_text = build_text_msg(shop ,response ,"" ,message ,{} ,history)
                                    mime_msg = create_mime_msg(sav_mail["BUFFALO"], message_text, message)
                                    gmail_request("BUFFALO" ,"post" ,"messages/send" ,endpoints="", post_data=mime_msg)
                                    file = open("shops/BUFFALO/history.csv" ,"a")
                                    content = "\n{},{},{},{},{}".format(message["email"] ,str(datetime.now())[:-7] ,"no"
                                                                        ,[] ,[])
                                    content += ",{}".format(shop)
                                    file.write(content)
                                    file.close()

                                append_message_id(message_id)
                                continue

                        # Get the owner:
                        for client in clients.keys():
                            if shop in clients[client]["shops"]:
                                owner = client
                                break
                        owner = "William"  # -----------------------

                        today_msg = clients[owner]["today_msg"]
                        today_nt = clients[owner]["today_nt"]
                        credit = clients[owner]["credit"]


                        if message == {"STARRED"}:
                            # update_clients_dic(clients,owner,today_msg+1,today_nt,credit-1)
                            append_message_id(message_id)
                            print("history saved ! waiting for another message\n")
                            # raise StarredError("This message is starred !")
                            continue

                        if message["source_language"] == "ERROR":
                            message_text = "I could not identify the client's language"
                            mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                            gmail_request(shop ,"post" ,"drafts" ,endpoints="", post_data={"message" :mime_msg})
                            put_a_star(shop, message)
                            today_nt += 1
                            print("history saved ! waiting for another message\n")
                            continue

                        score, menace = detect_irritation_score(message)
                        while "!!" in message["data"] or "??" in message["data"]:
                            message["data"] = message["data"].replace("!!" ,"!").replace("??" ,"?")

                        if message["data"] != "too_long":
                            message["order_name"] = detect_order_name(message)
                            print("new email received :\n{}".format(message))
                            questions = detect_question(message["data"] ,message["subject"])
                            print("questions :\n" + str(questions))
                            if not is_buffalo:
                                customer_id = shopify_get_customer(shop ,message ,history)
                            order_info = shopify_get_orders(shop ,message ,customer_id)
                            print("order infos :\n" + str(order_info))

                            if "thanks" in questions and "status" in questions:
                                questions = ["status" ,"none"]
                            if "thanks" in questions and "tracking_PB" in questions:
                                questions = ["tracking_PB" ,"none"]

                            if order_info != {}:
                                if questions[0] == "not_customer":
                                    questions[0] = "none"
                                if questions[1] == "not_customer":
                                    questions[1] = "none"

                                order_info["last_tracking_date"] = None
                                if order_info["status"] != "not_fulfilled":
                                    order_info = get_tracking(order_info)
                                order_info["time"], order_info["order_time"] = get_time(order_info)
                                print("better order infos detected :\n" + str(order_info))

                            response, answer_id = build_answer(shop ,order_info ,message ,questions ,history ,is_buffalo)

                            messenger_wait = answer_id in [CANCEL_ID ,REFUND_ID ,ADDRESS_ID] or menace or score > 70
                            if response != "no reply":
                                if "/ALERT" not in response:
                                    message_text = build_text_msg(shop ,response ,answer_id ,message ,order_info ,history)
                                    mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                                    if not messenger_wait:
                                        gmail_request(shop ,"post" ,"messages/send" ,endpoints="", post_data=mime_msg)
                                        # gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
                                    else:
                                        is_draft = False
                                else:
                                    message_text = response.replace("/ALERT " ,"")
                                    mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                                    if not messenger_wait:
                                        gmail_request(shop ,"post" ,"drafts" ,endpoints="", post_data={"message" :mime_msg})
                                        today_nt += 1
                                    else:
                                        is_draft = True

                                    put_a_star(shop, message)

                                if messenger_wait:
                                    file = open("clients/{}/messenger_cache.txt".format(owner) ,"r")
                                    messenger_cache = eval(file.read())
                                    file.close()
                                    messenger_cache[message["email"]] = [mime_msg ,is_draft]
                                    file = open("clients/{}/messenger_cache.txt".format(owner) ,"w")
                                    file.write(str(messenger_cache))
                                    file.close()

                                print("response :\n" + str(message_text))

                            # fb_new(shop,questions,order_info,message,answer_id,menace,score)

                        elif message["data"] == "too_long":
                            message_text = "This message is too complicated, maybe it's not from a customer."
                            mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                            gmail_request(shop ,"post" ,"drafts" ,endpoints="", post_data={"message" :mime_msg})
                            today_nt += 1
                    for kjkj in "a":
                        print("error on message {}".format(message_id))

                    ###################

                    # update_clients_dic(clients,owner,today_msg+1,today_nt,credit-1)

                    append_message_id(message_id)

                    print("history saved ! waiting for another message\n")
   