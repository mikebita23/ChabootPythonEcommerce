# -*- coding: utf-8 -*-
path = "D:/shopify/programmes/_SAV"

#######################################################
################ SAV V1.4 by W.SELLIER ################
#######################################################

import re
import time
import random
import string
import codecs
import html
import json
import base64
import requests
import apiai
import fbchat
from unidecode import unidecode
from datetime import datetime
from fbchat import Client, models
from email.mime.text import MIMEText

#######################################################

def gmail_request(shop,req_type,ressource,endpoints="",post_data={}):
    global user_id,api_key,client_id,client_secret,refresh_token,access_tokens
    tries = 0
    while tries < 20:
        try:
            cont = "https://www.googleapis.com/gmail/v1/users/{}/{}?{}key={}".format(user_id[shop],ressource,endpoints,api_key[shop])
            if req_type == "get":
                r = requests.get(cont,headers={"Authorization":"OAuth {}".format(access_tokens[shop])})
            elif req_type == "post":
                r = requests.post(cont,headers={"Authorization":"OAuth {}".format(access_tokens[shop])},json=post_data)
            if r.status_code > 300:
                data = {"client_id":client_id[shop],"client_secret":client_secret[shop],"refresh_token":refresh_token[shop],"grant_type":"refresh_token"}
                r2 = requests.post("https://www.googleapis.com/oauth2/v4/token",data=data)
                access_tokens[shop] = r2.json()["access_token"]
                continue #retry a request with a new access_token
            break
        except:
            print("connexion error on gmail, retrying...")
            time.sleep(10)
            tries += 1
    return r


def shopify_request(shop,req_type,ressource,endpoints="",put_data={}):
    global shopify_api_url
    if req_type == "get":
        r = requests.get("{}{}{}".format(shopify_api_url[shop],ressource,endpoints))
    elif req_type == "post":
        r = requests.post("{}{}{}".format(shopify_api_url[shop],ressource,endpoints), json = put_data)
    if req_type == "put":
        r = requests.put("{}{}{}".format(shopify_api_url[shop],ressource,endpoints), json = put_data)
    return r
    

def apiai_request(ai,text,session_id):
    request = ai.text_request()
    request.lang = 'fr'
    request.session_id = session_id
    request.query = text
    response = request.getresponse()
    s = json.loads(response.read().decode('utf-8'))
    rep_text = s["result"]["fulfillment"]["speech"]
    contexts = s["result"]["contexts"]
    return rep_text, contexts

########################################################

def shop_dic():
    file = open("{}/credentials.csv".format(path),"r")
    cont = file.read()
    file.close()
    lst2, shops = [], []
    shopify_api_url,first_customer,client_id,client_secret,refresh_token,user_id,api_key,sav_mail,img = {},{},{},{},{},{},{},{},{}
    lst = cont.split("\n")
    for i in range(len(lst)):
        lst2.append(lst[i].split(","))
    for k in range(1,len(lst2)):
        shop = lst2[k][0]
        shopify_api_url[shop] = lst2[k][1]
        first_customer[shop] = lst2[k][2]
        client_id[shop] = lst2[k][3]
        client_secret[shop] = lst2[k][4]
        refresh_token[shop] = lst2[k][5]
        user_id[shop] = lst2[k][6]
        api_key[shop] = lst2[k][7]
        sav_mail[shop] = lst2[k][8]
        img[shop] = lst2[k][9]
    for key in shopify_api_url.keys():
        shops.append(key)
    return shops,shopify_api_url,first_customer,client_id,client_secret,refresh_token,user_id,api_key,sav_mail,img


def build_clients_dic():
    file = open("{}/clients.csv".format(path),"r")
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
        dic[client[0]] = {"shops":shops, "thread_id":fb_thread_id, "today_msg":today_msg, "today_nt":today_nt, "credit":credit}
    return dic
    
    
def update_clients_dic(clients,owner,today_msg,today_nt,credit):
	for client in clients:
		if client == owner:
			clients[client]["today_msg"] = str(today_msg)
			clients[client]["today_nt"] = str(today_nt)
			clients[client]["credit"] = str(credit)
			break

	cont4 = ""
	for a in clients.keys():
		cont4 += "{},{},{}\n".format(a,";".join(clients[a]["shops"]),",".join(list([str(b) for b in clients[a].values()])[1:]))

	file = open("{}/clients.csv".format(path),"w")
	file.write(cont4[:-1])
	file.close()


def reset_clients_dic():
    clients = build_clients_dic()
    for client in clients.keys():
        clients[client]["today_msg"] = "0"
        clients[client]["today_nt"] = "0"

    cont4 = ""
    for a in clients.keys():
        cont4 += "{},{},{}\n".format(a,";".join(clients[a]["shops"]),",".join(list([str(b) for b in clients[a].values()])[1:]))
    file = open("{}/clients.csv".format(path),"w")
    file.write(cont4[:-1])
    file.close()


def token_dic(shops):
    access_tokens = {}
    for i in shops:
        access_tokens[i] = "init"
    return access_tokens


def build_messages_dic(shops):
    messages_dic_1, messages_dic_2 = {}, {}
    for n in range(1,3):
        for shop in shops:
            file = codecs.open("{}/{}/messages_dic_{}.csv".format(path,shop,n),encoding="utf-8")
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
    file = open("{}/{}/history.csv".format(path,shop),"r")
    cont = file.read()
    file.close()
    lst = cont.split("\n")
    for i in range(len(lst)):
        history.append(lst[i].split(","))
    return history


def order_ids_init(first_customer):
    first_order_ids = {}
    global shops
    for shop in shops:
        r1 = shopify_request(shop,"get","customers/search.json","?query={}&fields=id".format(first_customer[shop]))
        customer_id = r1.json()["customers"][0]["id"]
        r2 = shopify_request(shop,"get","customers/{}/orders.json".format(customer_id),"?status=any&fields=id")
        j = r2.json()
        first_order_ids[shop] = j["orders"][0]["id"]
    return first_order_ids
    
########################################################

def update_order_ids(shop,first_order_ids):
    file = open("{}/{}/order_ids.csv".format(path,shop),"r")
    init = file.read()
    file.close()
    new = ""
    if len(init) > 5:
        lst = init.split("\n")
        last_id = lst[len(lst)-1].split(",")[1]
        new = "\n"
    else:
        last_id = first_order_ids[shop]
    k = ""
    while k != "stop":
        r = shopify_request(shop,"get","orders.json","?since_id={}&status=any&limit=250&fields=id,name".format(last_id))
        j = r.json()
        n_orders = len(j["orders"])
        if n_orders == 0:
            return last_id
        for i in range(n_orders):
            order_id = j["orders"][i]["id"]
            order_name = j["orders"][i]["name"].replace("#","")
            new += "{},{}\n".format(order_name,order_id)
            if i == n_orders - 1:
                last_id = order_id
                if i != 249:
                    k = "stop"
        print("Updating order ids...")
    file2 = open("{}/{}/order_ids.csv".format(path,shop),"w")
    file2.write("{}{}".format(init,new[:len(new)-1]))
    file2.close()
    return last_id
    
#########################################################

def shopify_get_customer(shop,message,history):
    customer_id = "not found" #Default
    #First try : If the customer id is already in the history
    for l in history:
        if l[0] == message["email"] and l[2] != "no":
            return l[2]

    #Second try : Query in the shopify data        
    for query in [message["email"],message["full_name"]]:
        r1 = shopify_request(shop,"get","customers/search.json","?query={}".format(query))
        customers = r1.json()["customers"]
        if customers != [] and len(customers) == 1:
            customer_id = customers[0]["id"]
            break
    return str(customer_id)
    

def shopify_get_orders(shop,message,customer_id):
    if message["order_name"] != "not found":
        order_id = "not found"
        k = ""
        while k != "stop":
            file = open("{}/{}/order_ids.csv".format(path,shop),"r")
            order_ids = file.read()
            file.close()
            lst = order_ids.split("\n")
            for i in lst:
                lst2 = i.split(",")
                if lst2[0] == message["order_name"]:
                    order_id = lst2[1]
                    k = "stop"
            if order_id == "not found":
                update_order_ids(shop,first_order_ids)
                order_id == "new test"
                continue
            if order_id == "new test":
                return {}
        r = shopify_request(shop,"get","orders/{}.json".format(order_id),"?status=any&fields=total_price,fulfillments,created_at,name,customer")
        data = r.json()["order"]
    elif customer_id != "not found":
        r = shopify_request(shop,"get","customers/{}/orders.json".format(customer_id), "?status=any&fields=id,total_price,fulfillments,created_at,name,customer")
        
        data0 = r.json()["orders"]
        if data0 != []:
            data = data0[0]
            order_id = data["id"]
        else:
            return {}
    else:
        return {}
    order_info = {}
    order_info["order_id"] = order_id
    order_info["customer_id"] = str(data["customer"]["id"])
    order_info["date"] = shopify_date(data["created_at"])
    order_info["name"] = data["name"]
    order_info["total_price"] = str(data["total_price"])
    fulfillments = data["fulfillments"]
    if fulfillments != []:
        order_info["status"] = "fulfilled"
        order_info["fulfillment_date"] = shopify_date(fulfillments[0]["created_at"])
        order_info["tracking_num"] = fulfillments[0]["tracking_number"]
    else:
        order_info["status"] = "not_fulfilled"
    return order_info


def get_tracking(order_info):
    tracking_num = order_info["tracking_num"]
    order_info["last_tracking_date"] = None
    first_try_fail,second_try_fail = True,True
    patterns = {"(final delivery|has been delivered|was delivered|boîte à lettres du destinataire)":"delivered",
            "(arriv.+ dans le site en vue de sa distribution|delivery site)":"in_local_center",
            "(arriv.+ en france|roissy|paris)":"in_dest_country",
            "(quitt.+ son pays d'expédition|départ imminent du pays d'expédition|airline transit)":"in_airline",
            "(sorting center|sort facility|centre de tri)":"shipped"}
    headers = {"X-RapidAPI-Host":"apidojo-17track-v1.p.rapidapi.com","X-RapidAPI-Key":"c508fe71d1msheb8b2d50c6ccb1fp1bbe19jsn8c3440da85ae"}
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
                                first_try_fail = False
                                break2 = True
                                break
                        if break2:
                            break
            if order_info["status"] == "fulfilled":
                k += 1
                print("retrying 17track...")
                time.sleep(5)
            else:
                k = 2
    except:
        return order_info
    """
    if order_info["status"] == "fulfilled":
        print("can't find on 17track, trying on trackingmore please wait...")
        headers = {"Trackingmore-Api-Key":"ceb45110-5190-4656-9122-1797202ca32e"}
        r2 = requests.post("https://api.trackingmore.com/v2/carriers/detect",json={"tracking_number":tracking_num},headers=headers)
        code = r2.json()["data"][0]["code"]
        data = {"tracking_number":tracking_num,"carrier_code":code,"destination_code":"fr"}
        r3 = requests.post("https://api.trackingmore.com/v2/trackings/post",json=data,headers=headers)
        r4 = requests.get("https://api.trackingmore.com/v2/trackings/{}/{}".format(code,tracking_num),headers=headers)
        j = r4.json()["data"]
        if j != []:
            if (j["status"] != "notfound") and (j["status"] != "pending"):
                if j["origin_info"]["trackinfo"] != None:
                    lst = j["origin_info"]["trackinfo"]
                else:
                    lst = j["destination_info"]["trackinfo"]
                break2 = False
                for event in lst:
                    for pattern in patterns.keys():
                        match1 = re.search(pattern,event["StatusDescription"].lower())
                        match2 = re.search(pattern,event["checkpoint_status"].lower())
                        if match1 or match2:
                            order_info["status"] = patterns[pattern]
                            order_info["last_tracking_date"] = shopify_date(event["Date"])
                            second_try_fail = False
                            break2 = True
                            break
                    if break2:
                        break
    if first_try_fail and second_try_fail:
        order_info["last_tracking_date"] = None
    """
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
    time = times[status] - delta.days
    return time, order_time

###########################################################
   
def body_decoder(body):
	b64_char  = base64.urlsafe_b64decode(body)
	utf8_char = b64_char.decode("utf-8")
	html_char = html.unescape(utf8_char)
	html_char = html_char.replace("\r\n","\n").replace("\n",".")
	pattern1 = r"(Le|On).{15,30}:\d{2}.+"
	pattern2 = r"\-{10}.Forwarded.message.+"
	pattern3 = r"\.D(e|a)\s?:.+"
	pattern4 = r"Provenance :.+"
	pattern5 = r"Inviato da Posta.+"
	pattern6 = r"Message du.{5,20}:\d{2}.+"
	pattern7 = r"envoyé :.{20,300}de :.+"
	pattern8 = r"Merci pour votre achat !.+"
	for pattern in [pattern1,pattern2,pattern3,pattern4,pattern5,pattern6,pattern7,pattern8]:
		html_char = re.sub(pattern, "", html_char)
	if len(html_char) > 1000:
		return "too_long"
	pattern_html = r"\</*[^\>]*\>"
	decoded_body = re.sub(pattern_html, "", html_char)
	decoded_body = decoded_body.replace(u'\xa0', ' ')
	while "  " in decoded_body or ".." in decoded_body:
		decoded_body = decoded_body.replace("  "," ").replace("..",".")
	return decoded_body


def gmail_get_message(shop,msg_id):
    message = {}
    r = gmail_request(shop,"get","messages/{}".format(msg_id))
    j = r.json()
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
                if lst1["parts"][i]["body"]["data"] != "":
                    Data = lst1["parts"][i]["body"]["data"]
                    break

    pattern = r"\<([^\s@]+@[^\s\.]+\.[\S]+)\>"
    match = re.search(pattern,From)
    if match:
        message["email"] = match.group(1)
    else:
        message["email"] = From
    message["data"] = body_decoder(Data)
    full_name = re.sub(pattern,"",From)
    message["full_name"] = full_name
    lst = full_name.lower().split(" ")
    #try to get first name:
    message["first_name"] = ""
    for i in lst:
        if i in name_list:
            message["first_name"] = " " + i.capitalize().replace(" ","")
            break

    return message


def detect_order_name(message):
    for text in [message["subject"],message["data"]]:
        order_name = "not found"
        match = re.search(r"\D(\d{4})\D","{}{}{}".format("a",text,"a"))
        if match:
            num = int(match.group(1))
            if num < 2000 and num > 1000:
                order_name = str(num)
                break
    return order_name
    
    
def detect_irritation_score(message):
    lst1 = ("arnaque","escro","voleur","colere","colère","pas content","mecontent","mécontent","honte","inadmissible","fureur","furie","fache","fâche","rage","inacceptable","inexcusable")
    lst2 = ("plainte","justice","judiciaire","polic","flic","gendarmerie","demeure","avocat","tribunal")
    text = message["data"]
    pattern_1 = r"[A-Z]{2,}" ; pattern_2 = r"(!|\?){2,}"
    s1 = len(re.findall(pattern_1,text)) - len(re.findall(r"(RE|COMMANDE|MERCI)",text))
    s2 = len(re.findall(pattern_2,text))
    s3 = 0
    for word in lst1+lst2:
        s3 += len(re.findall(word,text.lower()))
    s4 = len(re.findall(r"!",text))
    score = round(((s1+s2*2+s3)**(1/2))*30+10*s4**(1/2))
    if score > 100:
        score = 100
    # MENACE DETECTION:
    menace = False
    for word in lst2:
        if re.search(word,text.lower()):
            menace = True
            
    return score, menace

##############################################################

def fb_login():
    file = open("{}/fb_login.txt".format(path),"r")
    cred = file.read().split(",")
    fb_client = Client(cred[0],cred[1])
    return fb_client


def fb_send(message,thread_id):
    global fb_client
    #thread_id = "2878681122206840"
    #thread_id = "2711656968863208"
    tries = 0
    while tries < 20:
        try:
            lines = message.split("/br")
            for line in lines:
                message_id = fb_client.send(models.Message(text=line), thread_id=thread_id, thread_type=models.ThreadType.GROUP)
                try:
                    fb_client.markAsDelivered(thread_id,message_id)
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
                return text, sender
            break
        except:
            print("connexion error on fbchat, retrying...")
            time.sleep(10)
            tries += 1
        
    return "",""


def shopify_date(date):
    date = date[:10]
    lst = date.split("-")
    return datetime(int(lst[0]),int(lst[1]),int(lst[2]))

########################################################

def detect_question(text,subject):
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
    phrases = re.split("\.|!|\?",text)
    for phrase in phrases:
        # Tests if the phrase contain characters:
        test = False
        for letter in string.ascii_letters:
            if letter in phrase:
                test = True
        if test == False:
            text = text.replace(phrase,"")
            continue # Go to next phrase
        intentName = req(phrase)
        if intentName not in intentList:
            questions.append(intentName)
            intentList.append(intentName)
    l = len(questions)
    if l == 0:
        pattern1 = r"Commande #\d{1,20} confirmée"
        pattern2 = r"Une commande #\d{1,20} est en transit"
        patterns = [pattern1,pattern2]
        default_subject = False
        for pattern in patterns:
            if re.search(pattern,subject):
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
        questions = ["Default Fallback Intent","none"]
    elif l == 1:
        questions.append("none")
    elif l == 3 and "thanks" in questions:
        questions.remove("thanks")
    elif l >= 3:
        for i in range(l-2):
            del questions[0]
    
    return questions
    
    
def detect_response(shop,questions,order_info,message,history):
    response = ["/ALERT Aucun cas de figure detecté"]    #Default
    answer_id = "s0"
    last_answer = False
    global messages_dic_1, messages_dic_2
    for l in history:
        if l[0] == message["email"]:
            if "s" in l[4]:
                last_answer = False
            else:
                last_answer = True
            last_answer_id = l[4]
            break
            
    if last_answer:
        lst = messages_dic_2[shop]
        for l in lst:
            if l[2] == [""]:
                c1 = (questions[0] in l[1]) or (questions[1] in l[1])
            else:
                c1 = ((questions[0] in l[1]) or (questions[0] in l[2])) and ((questions[1] in l[1]) or (questions[1] in l[2]) or (questions[1] == "none"))
            c2 = order_info["status"] in l[3]
            if l[4] == ['']:
                c3 = True
            else:
                c3 = (int(l[4][0]) <= order_info["time"]) and (int(l[4][1]) >= order_info["time"])
            if l[5] == ['']:
                c4 = True
            else:
                c4 = (int(l[5][0]) <= order_info["order_time"]) and (int(l[5][1]) >= order_info["order_time"])
            c5 = last_answer_id in l[0]
            if c1 and c2 and c3 and c4 and c5:
                response = l[6]
                answer_id = l[8][0]
                break
        if response == ["/ALERT Aucun cas de figure detecté"]:
            last_answer = False
    
    if not last_answer:
        lst = messages_dic_1[shop]
        for l in lst:
            if l[1] == [""]:
                c1 = (questions[0] in l[0]) or (questions[1] in l[0])
            else:
                c1 = ((questions[0] in l[0]) or (questions[0] in l[1])) and ((questions[1] in l[0]) or (questions[1] in l[1]) or (questions[1] == "none"))
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
    return response[0], answer_id

    
def build_answer(shop,order_info,message,questions,history):
    second_message_failed = False
    questions_2 = ["info_not_found","none"]

    # CASE 1: if the customer has already a question
    for j in range(len(history)):
        if (message["email"] in history[j]) and (history[j][2] == "no"):
            if order_info != {}:
                questions_2 = eval(history[j][3].replace("$",","))
                response, answer_id = detect_response(shop,questions_2,order_info,message,history)
                history[j][2] = order_info["customer_id"]
                history[j][4] = answer_id
                lst = []  #rebuild the file content
                for lst3 in history:
                    lst.append(",".join(lst3))
                cont = "\n".join(lst)
                file = open("{}/{}/history.csv".format(path,shop),"w")
                file.write(cont)
                file.close()
                return response, answer_id
            else:
                questions_2 = ["second_message_failed","none"]
                second_message_failed = True
    # CASE 2:
    if order_info == {}: 
        order_info_2 = {"status":"none","time":400,"order_time":400}
        response, answer_id = detect_response(shop,questions_2,order_info_2,message,history)
        info = "no"
    # CASE 3 : Normal case
    elif not second_message_failed:
        response, answer_id = detect_response(shop,questions,order_info,message,history)
        info = order_info["customer_id"]

    lst = []  #rebuild the file content
    for lst3 in history:
        lst.append(",".join(lst3))
    cont = "\n".join(lst)
    file = open("{}/{}/history.csv".format(path,shop),"w")
    file.write("{}\n{},{},{},{},{}".format(cont,message["email"],str(datetime.now())[:-7],info,str(questions).replace(",","$"),answer_id))
    file.close()
    return response, answer_id

###########################################

def create_mime_msg(sender, message_text, message):
    mime_msg = MIMEText(message_text, "html")
    mime_msg['to'] = message["email"]
    mime_msg['from'] = sender
    mime_msg['subject'] = "Re: {}".format(message["subject"])
    mime_msg['In-Reply-To'] = message["Message_ID"]
    mime_msg["References"] = message["Message_ID"]
    return {'raw':base64.urlsafe_b64encode(mime_msg.as_string().encode()).decode(), "threadId":message["threadId"]}


def build_text_msg(shop,response,answer_id,message,order_info,history):
    global img
    response2 = response.replace("$",",")
    if "tracking_num" in order_info.keys():
        response2 = response2.replace("{tracking_num}",order_info["tracking_num"])
    response2 = response2.replace("{first_name}",message["first_name"])
    
    now = datetime.now()
    if now.hour >= 19:
        hello = "Bonsoir"
        ends = ["Très bonne soirée", "Passez une bonne soirée", "Bien à vous"]
    else:
        ends = ["Très bonne journée", "Passez une bonne journée", "Bien à vous"]
        hello = "Bonjour"
    hello_msg = "{}{},<br><br>".format(hello,message["first_name"])
    for l in history:
        if l[0] == message["email"]:
            if shopify_date(l[1]).date() == now.date():
                hello_msg = ""
            break
        
    if "s" not in answer_id:
        end = ends[random.randint(0,len(ends)-1)]
        signature = "<br><br>{},<br><br>Lucie de l'équipe {}".format(end,shop)
    else:
        signature = "<br><br>Lucie de l'équipe {}".format(shop)
        
    message_text = "<img src=\"{}\" alt=\"\" /><p>{}{}{}</p>".format(img[shop],hello_msg,response2,signature)
    return message_text
    
    
def fb_new(shop,questions,order_info,message,answer_id,menace,score):
    if "modify_adress" in questions and order_info == {}:
        file = open("{}/{}/messages_cache.csv".format(path,shop),"r")
        cont = file.read()
        file.close()
        dic = eval(cont.replace("$",","))
        dic[message["email"]] = str(message).replace(",","$")
        file = open("{}/{}/messages_cache.csv".format(path,shop),"w")
        file.write(str(dic))
        file.close()
    
    if menace:
        answer_id = "menace"
        alert_msg = "Attention, je viens de recevoir un message d'un client qui menace de porter plainte !"
    elif score > 70:
        answer_id = "angry"
        alert_msg = "Attention, je viens de recevoir un message d'un client qui semble très en colère !"
    elif answer_id == "14":
        alert_msg = "Un client veut annuler sa commande et celle ci n'a pas encore été traitée."
    elif answer_id == "17.2":
        alert_msg = "Un client demande a être remboursé et n'a pas reçu sa commande depuis plus de 30 jours."
    else:
        alert_msg = ""
    
    if answer_id in ["14","17.2","19","menace","angry"]:
        global clients
        for owner in clients.keys():
            if shop in clients[owner]["shops"]:
                owner2 = owner
                thread_id = clients[owner]["thread_id"]
                break
        file = open("{}/clients/{}/messenger_assistant.csv".format(path,owner2),"r")
        cont = file.read()
        file.close()
        session_id = "ID{}".format("".join([str(random.randint(0,9)) for i in range(10)]))
        if cont == "":
            ai = apiai.ApiAI("5748c522a6614cd38896b9b704ea6462")
            phrase = "id {}".format(answer_id)
            rep_text, contexts = apiai_request(ai,phrase,session_id)
            if order_info != {}:
                text = build_fb_answer(shop,order_info,message,rep_text,"").replace("/alert_msg",alert_msg)
            else:
                text = "{} Son message : {} Malheureusement je ne l'ai pas retrouvé dans ta liste de clients. Je te laisse donc voir ça avec lui ! Son mail : {} , envoyé sur {}".format(alert_msg,message["data"],message["email"],shop)
                fb_send(text,thread_id)
                return None
            
        else:
            text = "Stp répond à mon précédent message, j'aurai d'autres trucs à te dire après ça"
            cont += "\n"
            
        fb_send(text,thread_id)
        
        actions = {"14":"refund","17.2":"refund","19":"modify_adress","menace":"menace","angry":"angry"}
        action = actions[answer_id]
            
        if order_info != {}:
            order_info["date"] = str(order_info["date"])
            if order_info["last_tracking_date"] != None:
                order_info["last_tracking_date"] = str(order_info["last_tracking_date"])
            if order_info["status"] != "not_fulfilled":
                order_info["fulfillment_date"] = str(order_info["fulfillment_date"])
            
        file = open("{}/{}/messages_cache.csv".format(path,shop),"r")
        cont2 = file.read()
        file.close()
        dic = eval(cont2.replace("$",","))
        if message["email"] in dic.keys():
            message = dic[message["email"]]
            
        file = open("{}/clients/{}/messenger_assistant.csv".format(path,owner),"w")
        file.write("{}{},{},{},{},{}".format(cont,session_id,action,shop,str(message).replace(",","$"),str(order_info).replace(",","$")))
        file.close()
        
    return None
    
    
def build_fb_answer(shop,order_info,message,rep_text,sender):
    global today_msg,today_nt,credit
    order_time = str(order_info["order_time"])
    order_name = order_info["name"]
    total_price = str(order_info["total_price"])
    if order_info["status"] == "not_fulfilled":
        tracking = "Cette commande est non traitée sur shopify !"
    else:
        tracking = "La commande a bien été expédiée il y a {} jours, voici son numéro de suivi : {}".format(order_time,order_info["tracking_num"])
    full_info = "Commande {}, passée il y a {} jours sur votre boutique {} pour un montant total de {}€. {}".format(order_name,order_time,shop,total_price,tracking)
    answer = rep_text
    answer = answer.replace("/message_name",message["full_name"])
    answer = answer.replace("/message_email",message["email"])
    answer = answer.replace("/message_data",message["data"])
    answer = answer.replace("/order_time",order_time)
    answer = answer.replace("/order_name",order_name)
    answer = answer.replace("/total_price",total_price)
    answer = answer.replace("/tracking",tracking)
    answer = answer.replace("/full_info",full_info)
    answer = answer.replace("/shop",shop)
    answer = answer.replace("/sender",sender)
    answer = answer.replace("/today_msg",str(today_msg))
    answer = answer.replace("/today_nt",str(today_nt))
    answer = answer.replace("/credit",str(credit))
    answer = answer.replace("il y a 0 jours","aujourd'hui")
    return answer


########################################


def shopify_modify_address(shop,contexts,order_id):
    for context in contexts:
        if context["name"] == "modify_adress-followup":
            if "parameters" in context.keys():
                parameters = context["parameters"]
                break
            else:
                return False
            
    r = shopify_request(shop,"get","orders/{}.json".format(order_id),"?status=any&fields=shipping_address")
    address = r.json()["order"]["shipping_address"]
    if "address" in parameters.keys():
        address["address1"] = parameters["address"]
        address["address2"] = ""
    elif "number" in parameters.keys():
        number = "{} ".format(parameters["number"])
        old = " {}".format(address["address1"])
        address["address1"] = re.sub(r"\D\d+\D", number, old_number)
    if "any" in parameters.keys():
        address["address2"] += parameters["any"]
    if "zip-code" in parameters.keys():
        zip_code = parameters["zip-code"]
        for zip in lst_zip_codes:
            if zip[0] == zip_code:
                address["city"] = zip[1]
                address["zip"] = zip_code
                break
    elif "geo-city" in parameters.keys():
        geo_city = parameters["geo-city"]
        for zip in lst_zip_codes:
            if zip[1] == unidecode(geo_city.upper().replace("-"," ").replace("'"," ")):
                address["city"] = geo_city
                address["zip"] = zip[0]
                break
                
    put_data = {"order":{"id":order_id, "shipping_address":address}}
    shopify_request(shop,"put","orders/{}.json".format(order_id),put_data=put_data)
    return True

def shopify_refund(shop,order_id):
    r = shopify_request(shop,"get","orders/{}.json".format(order_id),"?status=any&fields=line_items")
    line_items = r.json()["order"]["line_items"]
    line_items_2 = []
    for item in line_items:
        line_item_id = item["id"]
        quantity = item["quantity"]
        line_items_2.append({"line_item_id":line_item_id, "quantity":quantity, "restock_type":"no_restock"})
    put_data = {"refund":{"currency":"EUR","shipping":{"full_refund":True},"refund_line_items":line_items_2}}
    r2 = shopify_request(shop,"post","orders/{}/refunds/calculate.json".format(order_id),put_data=put_data)
    transactions = r2.json()["refund"]["transactions"]
    transactions_2 = []
    for transaction in transactions:
        del transaction["order_id"]
        del transaction["maximum_refundable"]
        transaction["currency"] = "EUR"
        transaction["kind"] = "refund"
        transactions_2.append(transaction)
    put_data = {"refund":{"currency":"EUR","notify":True,"shipping":{"full_refund":True},"refund_line_items":line_items_2,"transactions":transactions_2}}
    r3 = shopify_request(shop,"post","orders/{}/refunds.json".format(order_id),put_data=put_data)
    
    
def do_action(shop,owner,action,contexts,order_info,message):
    global clients
    today_msg = clients[owner]["today_msg"]
    today_nt = clients[owner]["today_nt"]
    credit = clients[owner]["credit"]
    
    file = open("{}/clients/{}/messenger_cache.txt".format(path,owner),"r")
    lst = eval(file.read())[message["email"]]
    mime_msg = lst[0]
    is_draft = lst[1]
    file.close()
    
    send = False
    if action == "modify_adress":
        send = shopify_modify_address(shop,contexts,order_info["order_id"])
    elif action == "angry" or action == "menace":
        for context in contexts:
            if context["name"] == "refund":
                shopify_refund(shop,order_info["order_id"])
                if is_draft:
                    message_text = "J'ai remboursé intégralement ce client"
                    mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                    gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
            if context["name"] == "send":
                send = True
            elif context["name"] == "draft":
                message_text = "Ce client semblait en colère, tu m'as demandé de ne pas traiter son message"
                mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
                today_nt += 1
                return None
    elif action == "refund":
        for context in contexts:
            if context["name"] == "refund":
                send = True
                shopify_refund(shop,order_info["order_id"])
            elif context["name"] == "draft":
                message_text = "Je pensais rembourser ce client mais tu m'as demandé de ne pas traiter son message"
                mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
                today_nt += 1
                return None
    if send:
        if not is_draft:
            gmail_request(shop,"post","messages/send",endpoints="", post_data=mime_msg)
            # gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
        else:
            gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
        
    update_clients_dic(clients,owner,today_msg+1,today_nt,credit-1)
    
    
############## EXCEPTIONS ##############

"""
def gmail_request(shop,req_type,ressource,endpoints="",post_data={}):
    try:
        return Gmail_request(shop,req_type,ressource,endpoints="",post_data={})
    except:
        raise
def shopify_request(shop,req_type,ressource,endpoints=""):
    try:
        return Shopify_request(shop,req_type,ressource,endpoints="")
    except:
        raise
def update_order_ids(shop,first_orders_id):
    try:
        return Update_order_ids(shop,first_orders_id)
    except:
        raise
def shopify_get_customer(shop,message,history):
    try:
        return Shopify_get_customer(shop,message,history)
    except:
        raise
def shopify_get_orders(shop,message,customer_id):
    try:
        return Shopify_get_orders(shop,message,customer_id)
    except:
        raise
def get_tracking(order_info):
    try:
        return Get_tracking(order_info)
    except:
        raise
def get_time(order_info):
    try:
        return Get_time(order_info)
    except:
        raise
def body_decoder(body):
    try:
        return Body_decoder(body)
    except:
        raise
def gmail_get_message(shop,msg_id):
    try:
        return Gmail_get_message(shop,msg_id)
    except:
        raise
def detect_question(text):
    try:
        return Detect_question(text)
    except:
        raise
def detect_response(shop,questions,order_info,history):
    try:
        return Detect_response(shop,questions,order_info,history)
    except:
        raise
def build_answer(shop,order_info,message,questions,history):
    try:
        return Build_answer(shop,order_info,message,questions,history)
    except:
        raise
def create_mime_msg(sender, message_text, message):
    try:
        return Create_mime_msg(sender, message_text, message)
    except:
        raise
"""

################ SCRIPT ################


fb_client = fb_login()

print("getting data...")

shops,shopify_api_url,first_customer,client_id,client_secret,refresh_token,user_id,api_key,sav_mail,img = shop_dic()
clients = build_clients_dic()
access_tokens = token_dic(shops)
messages_dic_1,messages_dic_2 = build_messages_dic(shops)
first_order_ids = order_ids_init(first_customer)

file = open("{}/message_ids.csv".format(path),"r")
cont_message_ids = file.read()
file.close()
lst_message_ids = cont_message_ids.split("\n")

file = open("{}/liste_prenom_FR_EN.txt".format(path),"r")
cont2 = file.read()
file.close()
name_list = cont2.split("\n")

file = open("{}/zip_codes_FR.csv".format(path),"r")
cont3 = file.read()
file.close()
lst = cont3.split("\n")
lst_zip_codes = []
for zip in lst:
    lst_zip_codes.append(zip.split(","))
lst = []

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
        # GMAIL:
        r = gmail_request(shop,"get","messages",endpoints="maxResults=1&q=label:inbox&")
        messages = r.json()["messages"]
        for message in messages:
            message_id = message["id"]
            if message_id not in lst_message_ids:
                
                # Update the files:
                shops,shopify_api_url,first_customer,client_id,client_secret,refresh_token,user_id,api_key,sav_mail,img = shop_dic()
                clients = build_clients_dic()
                messages_dic_1,messages_dic_2 = build_messages_dic(shops)
                first_order_ids = order_ids_init(first_customer)
                history = build_history(shop)
                
                # Get the owner:
                for client in clients.keys():
                    if shop in clients[client]["shops"]:
                        owner = client
                        break
                today_msg = clients[owner]["today_msg"]
                today_nt = clients[owner]["today_nt"]
                credit = clients[owner]["credit"]
                
                message = gmail_get_message(shop,message_id)
                score, menace = detect_irritation_score(message)
                while "!!" in message["data"] or "??" in message["data"]:
                    message["data"] = message["data"].replace("!!","!").replace("??","?")
                
                if message["data"] != "too_long":
                    message["order_name"] = detect_order_name(message)
                    print("new email received :\n{}".format(message))
                    questions = detect_question(message["data"],message["subject"])
                    print("questions :\n" + str(questions))
                    customer_id = shopify_get_customer(shop,message,history)
                    order_info = shopify_get_orders(shop,message,customer_id)
                    print("order infos :\n" + str(order_info))
                    
                    if order_info != {}:
                        order_info["last_tracking_date"] = None
                        if order_info["status"] != "not_fulfilled":
                            order_info = get_tracking(order_info)
                        order_info["time"], order_info["order_time"] = get_time(order_info)
                        print("better order infos detected :\n" + str(order_info))
                        
                    response, answer_id = build_answer(shop,order_info,message,questions,history)
                        
                    messenger_wait = answer_id in ["14","17.2","19"] or menace or score > 70
                    if response != "no reply":
                        if "/ALERT" not in response:
                            message_text = build_text_msg(shop,response,answer_id,message,order_info,history)
                            mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                            if not messenger_wait:
                                gmail_request(shop,"post","messages/send",endpoints="", post_data=mime_msg)
                                # gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
                            else:
                                is_draft = False
                        else:
                            message_text = response.replace("/ALERT ","")
                            mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                            if not messenger_wait:
                                gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
                                today_nt += 1
                            else:
                                is_draft = True
                                
                        if messenger_wait:
                            file = open("{}/clients/{}/messenger_cache.txt".format(path,owner),"r")
                            messenger_cache = eval(file.read())
                            file.close()
                            messenger_cache[message["email"]] = [mime_msg,is_draft]
                            file = open("{}/clients/{}/messenger_cache.txt".format(path,owner),"w")
                            file.write(str(messenger_cache))
                            file.close()
                            
                        print("response :\n" + str(message_text))
                    
                    fb_new(shop,questions,order_info,message,answer_id,menace,score)
                    
                elif message["data"] == "too_long":
                    message_text = "Ce message est trop long, il ne vient peut être pas d'un client."
                    mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                    gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
                    today_nt += 1
                
                ###################
                
                update_clients_dic(clients,owner,today_msg+1,today_nt,credit-1)
                    
                lst_message_ids.append(message_id)
                file = open("{}/message_ids.csv".format(path),"w")
                file.write("{}\n{}".format(cont_message_ids,message_id))
                file.close()
                print("history saved ! waiting for another message\n")

        # MESSENGER ASSISTANT:
        tries = 0
        while tries < 20:
            try:
                unreads = fb_client.fetchUnread()
                break
            except:
                print("connexion error on fbchat, retrying...")
                time.sleep(10)
                tries += 1
                
        if unreads != []:
            for thread_id in unreads:
                text,sender = fb_receive(thread_id)
                if text != None and sender != "Sav" and text[0] != "$":
                    clients = build_clients_dic()
                    for client in clients.keys():
                        if thread_id == clients[client]["thread_id"]:
                            owner = client
                            break
                    today_msg = clients[owner]["today_msg"]
                    today_nt = clients[owner]["today_nt"]
                    credit = clients[owner]["credit"]
                    
                    file = open("{}/clients/{}/messenger_assistant.csv".format(path,owner),"r")
                    cont = file.read()
                    file.close()
                    if cont == "":
                        ai = apiai.ApiAI("364a8762eb1345d9834b91c98b7e6efa")
                        rep_text, contexts = apiai_request(ai,text,"NONE")
                        shop = ""
                        order_info = {"order_time":"","name":"","total_price":"","status":"not_fulfilled"}
                        message = {"full_name":"","email":"","data":""}
                        answer = build_fb_answer(shop,order_info,message,rep_text,sender)
                        fb_send(answer,thread_id)
                    else:
                        lst = cont.split("\n")
                        lst2 = lst[0].split(",")
                        ai = apiai.ApiAI("5748c522a6614cd38896b9b704ea6462")
                        session_id = lst2[0]
                        rep_text, contexts = apiai_request(ai,text,session_id)
                        answer = rep_text
                        shop = lst2[2]
                        message = eval(lst2[3].replace("$",","))
                        order_info = eval(lst2[4].replace("$",","))
                        
                        answer = build_fb_answer(shop,order_info,message,rep_text,sender)
                        
                        if "/END" not in rep_text:
                            fb_send(answer,thread_id)
                            
                        else:
                            action = lst2[1]
                            answer = answer.replace("/END","")
                            fb_send(answer,thread_id)
                            do_action(shop,owner,action,contexts,order_info,message)
                        
                            cont2 = cont.replace(lst[0],"")[1:]

                            if cont2 != "":
                                while True:
                                    i = 1
                                    fb_send("Je voulais te prévenir d'autre chose :",thread_id)
                                    time.sleep(1)
                                    lst = cont2.split("\n")
                                    lst2 = lst[0].split(",")
                                    session_id = lst2[0]
                                    action = lst2[1]
                                    answer_id = action
                                    phrase = "assistant id {}".format(answer_id)
                                    rep_text, contexts = apiai_request(ai,phrase,session_id)
                                    shop = lst2[2]
                                    message = eval(lst2[3].replace("$",","))
                                    order_info = eval(lst2[4].replace("$",","))
                                    
                                    if action == "menace":
                                        alert_msg = "Attention, je viens de recevoir un message d'un client qui menace de porter plainte !"
                                    elif action == "angry":
                                        alert_msg = "Attention, je viens de recevoir un message d'un client qui semble très en colère !"
                                    else:
                                        alert_msg = ""
                                        
                                    if order_info != {}:
                                        answer = build_fb_answer(shop,order_info,message,rep_text,sender).replace("/alert_msg",alert_msg)
                                        fb_send(answer,thread_id)
                                        break
                                    else:
                                        answer = "{} Son message : /br {} /br Malheureusement je ne l'ai pas retrouvé dans ta liste de clients. Je te laisse donc voir ça avec lui ! Son mail : {} , envoyé sur {}".format(alert_msg,message["data"],message["email"],shop)
                                        fb_send(answer,thread_id)
                                        while cont2 != "":
                                            cont2 = cont2.replace(lst[i],"")[1:]
                                        i += 1
                    
                            file = open("{}/clients/{}/messenger_assistant.csv".format(path,owner),"w")
                            file.write(cont2)
                            file.close()
                            
                else:
                    try:
                        fb_client.markAsRead(thread_id)
                    except:
                        time.sleep(1)
                        

                        
                        
                        

