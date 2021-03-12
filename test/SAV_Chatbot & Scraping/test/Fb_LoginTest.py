import base64
import codecs

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
from test.Gmail_ResquestTest import Shopify


class QuestionTest(Shopify):
    def fb_login(self):
        file = open("fb_login.txt" ,"r")
        cred = file.read().split(",")
        fb_client = Client(cred[0] ,cred[1])
        return fb_client


    def fb_send(message ,thread_id):
        global fb_client
        # thread_id = "2878681122206840"
        # thread_id = "2711656968863208"
        tries = 0
        while tries < 20:
            try:
                lines = message.split("/br")
                for line in lines:
                    message_id = fb_client.send(models.Message(text=line), thread_id=thread_id, thread_type=models.ThreadType.GROUP)
                    try:
                        fb_client.markAsDelivered(thread_id ,message_id)
                        fb_client.markAsRead(thread_id)
                        time.sleep(1)
                    except:
                        time.sleep(1)
                break
            except:
                print("connexion error on fbchat send, retrying...")
                time.sleep(10)
                tries += 1
        return None


    def fb_receive(thread_id):
        global fb_client
        tries = 0
        while tries < 20:
            try:
                messages = fb_client.fetchThreadMessages(thread_id=thread_id, limit=1)
                message = messages[0]
                if not message.is_read:
                    user_id = message.author
                    user = fb_client.fetchUserInfo(user_id)[user_id]
                    sender = user.first_name
                    text = message.text
                    try:
                        fb_client.markAsRead(thread_id)
                    except:
                        time.sleep(1)
                    if text == "":  # Photo error
                        text = "$"

                    return text, sender
                break
            except:
                print("connexion error on fbchat, retrying...")
                time.sleep(10)
                tries += 1

        return "$" ,""


    def shopify_date(date):
        date = date[:10]
        lst = date.split("-")
        return datetime(int(lst[0]) ,int(lst[1]) ,int(lst[2]))
