import base64
import codecs
import json
import string
from typing import re

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
from test.Gmail_ResquestTest import Shopify


def detect_response(shop, questions_2, order_info_2, message, history):
    pass


class QuestionTest(Shopify):
    def detect_question(text ,subject):
        questions = []
        intentList = ["Default Fallback Intent"]
        ai = apiai.ApiAI("e0528ce03baf4b058a3585b7c54165e8")
        ########
        def req(phrase):
            request = ai.text_request()
            request.lang = 'fr'
            request.session_id = "RANDOM"
            request.query = phrase
            question = request.getresponse()
            s = json.loads(question.read().decode('utf-8'))
            try:
                intentName = s["result"]["metadata"]["intentName"]
            except:
                intentName = "Default Fallback Intent"
            return intentName
        ########
        phrases = re.split("\.|!|\?" ,text)
        for phrase in phrases:
            # Tests if the phrase contain characters:
            test = False
            for letter in string.ascii_letters:
                if letter in phrase:
                    test = True
            if test == False:
                text = text.replace(phrase ,"")
                continue # Go to next phrase
            intentName = req(phrase)
            if intentName not in intentList:
                questions.append(intentName)
                intentList.append(intentName)
        l = len(questions)
        if l == 0:
            pattern1 = r"Commande #\d{1,20} confirmée"
            pattern2 = r"Une commande #\d{1,20} est en transit"
            patterns = [pattern1 ,pattern2]
            default_subject = False
            for pattern in patterns:
                if re.search(pattern ,subject):
                    default_subject = True
                    break
            if not default_subject:
                for letter in string.ascii_letters:
                    if letter in subject:
                        intentName = req(subject)
                        if intentName not in intentList:
                            questions.append(intentName)
                            l += 1
                            break
        if l == 0:
            questions = ["Default Fallback Intent" ,"none"]
        elif l == 1:
            questions.append("none")
        elif l == 3 and "thanks" in questions:
            questions.remove("thanks")
        elif l >= 3:
            for i in range( l -2):
                del questions[0]

        return questions


    def detect_response(shop ,questions ,order_info ,message ,history):
        response = ["/ALERT No cases detected, I don't know what to answer"]  # Default
        answer_id = "s0"
        last_answer = False
        global messages_dic_1, messages_dic_2

        for l in history:
            if l[0] == message["email"]:
                if "s" in l[4]:
                    last_answer = False
                else:
                    last_answer = True
                answer_ids = list(eval(l[4].replace("$" ,",")))
                last_answer_id = answer_ids[-1]
                break

        if last_answer:
            lst = messages_dic_2[shop]
            for l in lst:
                if l[2] == [""]:
                    c1 = (questions[0] in l[1]) or (questions[1] in l[1])
                else:
                    c1 = ((questions[0] in l[1]) or (questions[0] in l[2])) and \
                                ((questions[1] in l[1]) or (questions[1] in l[2]) or (questions[1] == "none"))
                c2 = order_info["status"] in l[3]
                if l[4] == ['']:
                    c3 = True
                else:
                    c3 = (int(l[4][0]) <= order_info["time"]) and (int(l[4][1]) >= order_info["time"])
                if l[5] == ['']:
                    c4 = True
                else:
                    c4 = (int(l[5][0]) <= order_info["order_time"]) and (int(l[5][1]) >= order_info["order_time"])
                c5 = last_answer_id in l[0] or l[0] == ""
                if c1 and c2 and c3 and c4 and c5:
                    response = l[6]
                    answer_id = l[8][0]
                    break
            if response == ["/ALERT No cases detected, I don't know what to answer"]:
                last_answer = False

        if not last_answer:
            lst = messages_dic_1[shop]
            for l in lst:
                if l[1] == [""]:
                    c1 = (questions[0] in l[0]) or (questions[1] in l[0])
                else:
                    c1 = ((questions[0] in l[0]) or (questions[0] in l[1])) and (
                                (questions[1] in l[0]) or (questions[1] in l[1]) or (questions[1] == "none"))
                c2 = order_info["status"] in l[2]
                if l[3] == ['']:
                    c3 = True
                else:
                    c3 = (int(l[3][0]) <= order_info["time"]) and (int(l[3][1]) >= order_info["time"])
                if l[4] == ['']:
                    c4 = True
                else:
                    c4 = (int(l[4][0]) <= order_info["order_time"]) and (int(l[4][1]) >= order_info["order_time"])
                if c1 and c2 and c3 and c4:
                    response = l[6]
                    answer_id = l[9][0]
                    break
        return response[0], answer_id.replace("\r", "")


    def build_answer(shop, order_info, message, questions, history, is_buffalo):
        questions_2 = ["info_not_found", "none"]
        history_line = None

        # CASE 1: if the customer has already a question
        for j in range(len(history)):
            if (message["email"] in history[j]):
                if history[j][2] == "no":  # Question and then customer_id
                    questions_2 = eval(history[j][3].replace("$", ","))
                    if order_info != {}:
                        response, answer_id = shop.detect_response(shop, questions_2, order_info, message, history)
                        history[j][2] = order_info["customer_id"]

                    elif "not_customer" in questions and "status" in questions_2:
                        question_2 = ["status", "not_customer"]
                        order_info_2 = {"status": "none", "time": 400, "order_time": 400}
                        response, answer_id = shop.detect_response(shop, questions_2, order_info_2, message, history)

                    else:
                        response = "/ALERT I could not find info on this customer"
                        answer_id = "s9"

                elif order_info != {}:
                    response, answer_id = shop.detect_response(shop, questions, order_info, message, history)
                else:
                    response = "/ALERT I could not find info on this customer"
                    answer_id = "s9"

                answer_ids = list(eval(history[j][4].replace("$", ",")))
                if answer_id not in answer_ids:
                    answer_ids.append(answer_id)
                else:
                    return "/ALERT This customer often asks me the same question", "/ALERT"
                history[j][4] = str(answer_ids)
                lst = []  # rebuild the file content
                for lst3 in history:
                    lst.append(",".join(lst3))
                cont = "\n".join(lst)
                file = open("shops/{}/history.csv".format(shop), "w")
                file.write(cont)
                file.close()
                return response, answer_id

        """
        # CASE 2:
        if order_info == {} and "paypal" not in questions: 
            order_info_2 = {"status":"none","time":400,"order_time":400}
            response, answer_id = detect_response(shop,questions_2,order_info_2,message,history)
            info = "no"
        # CASE 3:
        elif order_info == {} and "paypal" in questions:
            order_info_2 = {"status":"none","time":400,"order_time":400}
            questions_2 = ["paypal","none"]
            response, answer_id = detect_response(shop,questions_2,order_info_2,message,history)
            info = "no"
        """

        # CASE 4 : First question
        if order_info != {}:
            response, answer_id = shop.detect_response(shop, questions, order_info, message, history)
            info = order_info["customer_id"]

        else:
            order_info_2 = {"status": "none", "time": 400, "order_time": 400}
            response, answer_id = detect_response(shop, questions_2, order_info_2, message, history)
            info = "no"
        # Build the file content
        answer_ids = []
        answer_ids.append(answer_id)
        if is_buffalo:
            shop = "BUFFALO"
        file = open("shops/{}/history.csv".format(shop), "a")
        content = "\n{},{},{},{},{}".format(message["email"], str(datetime.now())[:-7], info,
                                            str(questions).replace(",", "$"),
                                            str(answer_ids).replace(",", "$").replace("\r", ""))
        if is_buffalo:
            content += ",{}".format(shop)
        file.write(content)
        file.close()
        return response, answer_id
