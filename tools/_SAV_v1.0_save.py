# -*- coding: utf-8 -*-
path = "D:/shopify/programmes/_SAV"

#######################################################
################ SAV V1.0 by W.SELLIER ################
#######################################################

import re
import time
import string
import codecs
from datetime import datetime
import html
import json
import base64
import requests
import apiai
import fbchat
from fbchat import Client, models
from email.mime.text import MIMEText

#######################################################

def gmail_request(shop,req_type,ressource,endpoints="",post_data={}):
    global user_id,api_key,client_id,client_secret,refresh_token,access_tokens
    while True:
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
        return r


def shopify_request(shop,req_type,ressource,endpoints=""):
    global shopify_api_url
    if req_type == "get":
        r = requests.get("{}{}{}".format(shopify_api_url[shop],ressource,endpoints))
    if req_type == "post":
        r = requests.post("{}{}{}".format(shopify_api_url[shop],ressource,endpoints))
    return r

########################################################

def shop_dic():
    file = open("{}/credentials.csv".format(path),"r")
    cont = file.read()
    file.close()
    lst2, shops = [], []
    shopify_api_url,first_customer,client_id,client_secret,refresh_token,user_id,api_key = {},{},{},{},{},{},{}
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
    for key in shopify_api_url.keys():
        shops.append(key)
    return shops,shopify_api_url,first_customer,client_id,client_secret,refresh_token,user_id,api_key


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
        first_order_ids[shop] = j["orders"][len(j)-1]["id"]
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
        r = shopify_request(shop,"get","orders/{}.json".format(order_id),"?status=any&fields=fulfillments,created_at,name,customer")
        data = r.json()["order"]
    elif customer_id != "not found":
        r = shopify_request(shop,"get","customers/{}/orders.json".format(customer_id),"?status=any&fields=fulfillments,created_at,name,customer")
        data = r.json()["orders"][0]
    else:
        return {}
    order_info = {}
    order_info["customer_id"] = str(data["customer"]["id"])
    order_info["date"] = shopify_date(data["created_at"])
    order_info["name"] = data["name"]
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
    headers = {"X-RapidAPI-Host":"apidojo-17track-v1.p.rapidapi.com","X-RapidAPI-Key":"c508fe71d1msheb8b2d50c6ccb1fp1bbe19jsn8c3440da85ae"}
    r = requests.get("https://apidojo-17track-v1.p.rapidapi.com/track?codes={}".format(tracking_num),headers=headers)
    j = r.json()["dat"][0]["track"]
    patterns = {"(final delivery|has been delivered|was delivered|boîte à lettres du destinataire)":"delivered",
            "(arriv.+ dans le site en vue de sa distribution|delivery site)":"in_local_center",
            "(arriv.+ en france|roissy|paris)":"in_dest_country",
            "(quitt.+ son pays d'expédition|départ imminent du pays d'expédition|airline transit)":"in_airline",
            "(sorting center|sort facility|centre de tri)":"shipped"}
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
    times = {"not_fulfilled":100,"fulfilled":20,"shipped":18,"in_airline":12,"in_dest_country":6,"in_local_center":3,"delivered":0}
    status = order_info["status"]
    if order_info["last_tracking_date"] != None:
        delta = now - order_info["last_tracking_date"]
    elif status != "not_fulfilled":
        delta = now - order_info["fulfillment_date"]
    else:
        delta = now - order_info["date"]
    time = times[status] - delta.days
    return time

###########################################################
   
def body_decoder(body):
	b64_char  = base64.urlsafe_b64decode(body)
	utf8_char = b64_char.decode("utf-8")
	html_char = html.unescape(utf8_char)
	html_char = html_char.replace("\r\n","\n").replace("\n",".")
	pattern1 = r"Le.{15,25}à.{2,5}:\d{2}\,.+"
	pattern2 = r"\-{10}.Forwarded.message.+"
	html_char = re.sub(pattern1, "", html_char)
	html_char = re.sub(pattern2, "", html_char)
	if len(html_char) > 500:
		return "too_long"
	pattern3 = r"\</*[^\>]*\>"
	decoded_body = re.sub(pattern3, "", html_char)
	decoded_body = decoded_body.replace(u'\xa0', ' ')
	for i in range(8):
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
        match = re.search(r"\D(\d{5})\D",text+"to prevent a bug")
        if match:
            num = int(match.group(1))
            if num < 60000 and num > 40000:
                order_name = str(num)
                break
    return order_name
    
    
def detect_irritation_score(message):
    lst1 = ("arnaque","escro","voleur","colere","colère","pas content","mecontent","mécontent","honte","inadmissible","fureur","furie","fache","fâche","rage","inacceptable","inexcusable")
    lst2 = ("plainte","justice","judiciaire","polic","gendarmerie","demeure","avocat","tribunal")
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

def apiai_login():
    apiai_token = "e0528ce03baf4b058a3585b7c54165e8"
    ai = apiai.ApiAI(apiai_token)
    return ai


def fb_login():
    file = open("{}/fb_login.txt".format(path),"r")
    cred = file.read().split(",")
    fb_client = Client(cred[0],cred[1])
    return fb_client


def fb_send(fb_client,message):
    #thread_id = "2878681122206840"
    thread_id = "2711656968863208"
    message_id = fb_client.send(models.Message(text=message), thread_id=thread_id, thread_type=models.ThreadType.GROUP)
    fb_client.markAsDelivered(thread_id,message_id)
    fb_client.markAsRead(thread_id)
    return None


def fb_receive(fb_client):
    thread_id="2711656968863208"
    messages = fb_client.fetchThreadMessages(thread_id=thread_id, limit=1)
    message = messages[0]
    if not message.is_read:
        fb_client.markAsRead(thread_id)
        user_id = message.author
        user = fb_client.fetchUserInfo(user_id)[user_id]
        sender = user.first_name
        text = message.text
        return text, sender
    return "",""


def shopify_date(date):
    date = date[:10]
    lst = date.split("-")
    return datetime(int(lst[0]),int(lst[1]),int(lst[2]))

########################################################

def detect_question(text):
    questions = []
    intentList = ["Default Fallback Intent"]
    parameter_required = {"modify_adress":[],"modify_order":[]}
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
            parameters = s["result"]["parameters"]
        except:
            intentName = "Default Fallback Intent"
            parameters = {}
        return intentName, parameters
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
        intentName, parameters = req(phrase)
        if intentName not in parameter_required.keys():
            text = text.replace(phrase,"")
            if intentName not in intentList:
                questions.append([intentName,parameters])
                intentList.append(intentName)
    if "e" in text:
        intentName, parameters = req(text)
        questions.append([intentName,parameters])
    l = len(questions)
    if l == 0:
        questions = [["Default Fallback Intent",{}],["none",{}]]
    elif l == 1:
        questions.append(["none",{}])
    elif l >= 3:
        for i in range(l-2):
            del questions[0]
    
    return questions
    
    
def detect_response(shop,questions,order_info,message,history):
    response = "/ALERT Aucun cas de figure detecté"    #Default
    answer_id = 0
    last_answer = False
    global messages_dic_1, messages_dic_2
    for l in history:
        if l[0] == message["email"]:
            if l[4] == 0:
                last_answer = False
                last_answer_id = 0
            else:
                last_answer = True
                last_answer_id = l[4]
            break
            
    if last_answer:
        lst = messages_dic_2[shop]
        for l in lst:
            #c1 = ((questions[0][0] in l[1]) or (questions[1][0] in l[1])) and ((questions[0][0] in l[2]) or (questions[1][0] in l[2]) or (l[2][0]=="") or (questions[1][0]=="none"))
            c1 = ((questions[0][0] in l[1]) or (questions[0][0] in l[2])) and ((questions[1][0] in l[1]) or (questions[1][0] in l[2]) or (l[2][0]=="") or (questions[1][0]=="none"))
            c2 = order_info["status"] in l[3]
            c3 = (int(l[4][0]) <= order_info["time"]) and (int(l[4][1]) >= order_info["time"])
            c4 = last_answer_id in l[0]
            if c1 and c2 and c3 and c4:
                response = l[5]
                answer_id = l[7][0]
                break
        if response == "/ALERT Aucun cas de figure detecté":
            last_answer = False
    
    if not last_answer:
        lst = messages_dic_1[shop]
        for l in lst:
            #c1 = ((questions[0][0] in l[0]) or (questions[1][0] in l[0])) and ((questions[0][0] in l[1]) or (questions[1][0] in l[1]) or (l[1][0]=="") or (questions[1][0]=="none"))
            c1 = ((questions[0][0] in l[0]) or (questions[0][0] in l[1])) and ((questions[1][0] in l[0]) or (questions[1][0] in l[1]) or (l[1][0]=="") or (questions[1][0]=="none"))
            c2 = order_info["status"] in l[2]
            c3 = (int(l[3][0]) <= order_info["time"]) and (int(l[3][1]) >= order_info["time"])
            if c1 and c2 and c3:
                response = l[6]
                answer_id = l[9][0]
                break
    return response, answer_id

    
def build_answer(shop,order_info,message,questions,history):
    second_message_failed = False
    questions_2 = [["info_not_found",{}],["none",{}]]

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
                return response
            else:
                questions_2 = [["second_message_failed",{}],["none",{}]]
                second_message_failed = True
    # CASE 2:
    if order_info == {}:
        order_info_2 = {"status":"none","time":400}
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
    return response

###########################################

def create_mime_msg(sender, message_text, message):
    mime_msg = MIMEText(message_text, "html")
    mime_msg['to'] = message["email"]
    mime_msg['from'] = sender
    mime_msg['subject'] = "Re: {}".format(message["subject"])
    mime_msg['In-Reply-To'] = message["Message_ID"]
    mime_msg["References"] = message["Message_ID"]
    return {'raw':base64.urlsafe_b64encode(mime_msg.as_string().encode()).decode(), "threadId":message["threadId"]}


def build_text_msg(shop,response,message,order_info):
    #file = open()
    response2 = response[0].replace("$",",")
    if "tracking_num" in order_info.keys():
        response2 = response2.replace("{tracking_num}",order_info["tracking_num"])
    response2 = response2.replace("{first_name}",message["first_name"])
    message_text = "<p>Bonjour{},<br><br>{}<br><br>Très bonne journée,<br><br>Lucie de l'équipe Modernecil</p>".format(message["first_name"],response2)
    return message_text
    
    
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


#fb_client = fb_login()
ai = apiai_login()

print("getting data...")

shops,shopify_api_url,first_customer,client_id,client_secret,refresh_token,user_id,api_key = shop_dic()
access_tokens = token_dic(shops)
messages_dic_1,messages_dic_2 = build_messages_dic(shops)
first_order_ids = order_ids_init(first_customer)

file = open("{}/message_ids.csv".format(path),"r")
cont = file.read()
file.close()
lst_message_ids = cont.split("\n")

file = open("{}/liste_prenom_FR_EN.txt".format(path),"r")
cont2 = file.read()
file.close()
name_list = cont2.split("\n")

print("get data sucessful.\nWaiting for a new message")

while True:
    for shop in shops:
        # GMAIL:
        r = gmail_request(shop,"get","messages",endpoints="maxResults=1&q=label:inbox&")
        messages = r.json()["messages"]
        for message in messages:
            message_id = message["id"]
            if message_id not in lst_message_ids:
                
                #### STRUCTURE ####
                
                message = gmail_get_message(shop,message_id)
                score, menace = detect_irritation_score(message)
                for i in range(4):
                    message["data"].replace("!!","!").replace("??","?")
                
                if message["data"] != "too_long" and menace == False and score <= 70:
                    history = build_history(shop)
                    message["order_name"] = detect_order_name(message)
                    print("new email received :")
                    print(message)
                    questions = detect_question(message["data"])
                    print("questions :\n" + str(questions))
                    customer_id = shopify_get_customer(shop,message,history)
                    order_info = shopify_get_orders(shop,message,customer_id)
                    print("order infos :\n" + str(order_info))
                    if order_info != {}:
                        order_info["last_tracking_date"] = None
                        if order_info["status"] != "not_fulfilled":
                            order_info = get_tracking(order_info)
                        order_info["time"] = get_time(order_info)
                        print("better order infos detected :\n" + str(order_info))
                    response = build_answer(shop,order_info,message,questions,history)
                    if response != "no reply":
                        if "/ALERT" not in response:
                            message_text = build_text_msg(shop,response,message,order_info)
                            mime_msg = create_mime_msg("modernecil@gmail.com", message_text, message)
                            #gmail_request(shop,"post","messages/send",endpoints="", post_data=mime_msg)
                            gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
                        else:
                            message_text = response.replace("/ALERT ","")
                            mime_msg = create_mime_msg("modernecil@gmail.com", message_text, message)
                            gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
                        print("response :\n" + str(message_text))
                    
                elif message["data"] == "too_long":
                    message_text = "I think it is not a customer, so I didn't reply."
                    mime_msg = create_mime_msg("modernecil@gmail.com", message_text, message)
                    gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
                    
                elif menace == True:
                    alert = "Attention, je viens de recevoir un message d'un client qui menace de porter plainte ! Je vous laisse voir ca avec lui : {}    et voici son mail : {}".format(message["full_name"],message["email"])
                    print("sending to messenger :{}".format(alert))
                    #fb_send(fb_client,alert)
                    
                elif score > 70:
                    alert = "Vous avez un client qui semble vraiment en colère : {}    Je n'ose pas traiter son message de peur de le brusquer ! ^_^ ".format(message["email"])
                    print("sending to messenger :{}".format(alert))
                    #fb_send(fb_client,alert)
                
                ###################
                    
                lst_message_ids.append(message_id)
                cont += "\n{}".format(message_id)
                file = open("{}/message_ids.csv".format(path),"w")
                file.write("{}\n{}".format(cont,message_id))
                file.close()
                print("history saved ! waiting for another message\n")

        # MESSENGER ASSISTANT:
        """
        text,sender = fb_receive(fb_client)
        if text != "" and sender != "Sav":
            default_msg = "Désolé {}, mon developpeur ne m'a pas encore appris à répondre aux humains sur messenger :( Mais cela devrait être possible dans quelques jours ;)".format(sender)
            fb_send(fb_client,default_msg)
            #file = open("D:/shopify/programmes/_SAV/messages_fb","r")
            #cont2 = file.read()
            #file.close()
        """

"""
A faire:

supprimer paramètres intent

"""

