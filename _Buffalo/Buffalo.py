# -*- coding: utf-8 -*-

import re
import requests
import time
import random
import html
import json
import codecs
from unidecode import unidecode
from datetime import datetime
from email.mime.text import MIMEText

EMAIL = "contact.buffalo.pro@gmail.com"
CLIENT_ID + "237391394990-92bmcjsn4gm6nggca6bc418vu8rgvfko.apps.googleusercontent.com"
CLIENT_SECRET = "IpCT4JBRvzEs0HixUBafeQsy"
REFRESH_TOKEN = "1//03H69KyeAvGV9CgYIARAAGAMSNwF-L9IrozfO-o_BfntmH7xcp1bpQ5Dg143UAnNRJwYhWnQynsXWjOaRNUeA0oiJgdL_zYELn90"
API_KEY = "AIzaSyDI5GgNKGSFlqFG7kraxpT_Nb7hOMnkLLg"
ACCESS_TOKEN = "init"


def gmail_request(req_type,ressource,endpoints="",post_data={}):
    global EMAIL,USER_ID,API_KEY,CLIENT_ID,CLIENT_SECRET,REFRESH_TOKEN,ACCESS_TOKEN
    tries = 0
    while tries < 20:
        try:
            cont = "https://www.googleapis.com/gmail/v1/users/{}/{}?{}key={}".format(EMAIL,ressource,endpoints,API_KEY)
            if req_type == "get":
                r = requests.get(cont,headers={"Authorization":"OAuth {}".format(ACCESS_TOKEN)})
            elif req_type == "post":
                r = requests.post(cont,headers={"Authorization":"OAuth {}".format(ACCESS_TOKEN)},json=post_data)
            if r.status_code > 300:
                data = {"client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,"refresh_token":REFRESH_TOKEN,"grant_type":"refresh_token"}
                r2 = requests.post("https://www.googleapis.com/oauth2/v4/token",data=data)
                ACCESS_TOKEN = r2.json()["access_token"]
                continue #retry a request with a new access_token
            break
        except:
            print("connexion error on gmail, retrying...")
            time.sleep(10)
            tries += 1
    return r
    
    
def apiai_request(ai,text,session_id,contexts=[]):
    request = ai.text_request()
    request.lang = 'fr'
    request.session_id = session_id
    request.query = text
    if contexts != []:
        request.contexts = contexts
    response = request.getresponse()
    s = json.loads(response.read().decode('utf-8'))
    rep_text = s["result"]["fulfillment"]["speech"]
    contexts = s["result"]["contexts"]
    return rep_text, contexts
    
    
def build_messages_dic():
    messages_dic_1, messages_dic_2 = {}, {}
    for n in range(1,3):
        file = codecs.open("messages_dic_{}.csv".format(n),encoding="utf-8")
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
            messages_dic_1 = lst2
        elif n == 2:
            messages_dic_2 = lst2
    return messages_dic_1, messages_dic_2
    
    
def build_history():
    history = []
    file = open("history.csv","r")
    cont = file.read()
    file.close()
    lst = cont.split("\n")
    for i in range(len(lst)-1,-1,-1):
        history.append(lst[i].split(","))
    return history
    

def append_message_id(message_id):
    global lst_message_ids
    lst_message_ids.append(message_id)
    file = open("message_ids.csv","a")
    file.write("\n{}".format(message_id))
    file.close()
    
    
def put_a_star(message):
    thread_id = message["threadId"]
    post_data = {"addLabelIds": ["STARRED"]}
    gmail_request("post","threads/{}/modify".format(thread_id), post_data=post_data)
    
    
def body_decoder(body):
	b64_char  = base64.urlsafe_b64decode(body)
	utf8_char = b64_char.decode("utf-8")
	html_char = html.unescape(utf8_char)
	html_char = html_char.replace("\r\n","\n").replace("\n",".")
	pattern1 = r"(Le|On).{15,30}:\d{2}.+"  
	pattern2 = r"(Le|On).{20,120}(a écrit|wrote).+"
	pattern3 = r"\-{10}.Forwarded.message.+"
	pattern4 = r"(De|Da|From)\s?:.+"
	pattern5 = r"Provenance :.+"
	pattern6 = r"Inviato da Posta.+"
	pattern7 = r"Message du.{5,20}:\d{2}.+"
	pattern8 = r"envoyé :.{20,300}de :.+"
	pattern9 = r"Merci pour votre achat !.+"
	for pattern in [pattern1,pattern2,pattern3,pattern4,pattern5,pattern6,pattern7,pattern8,pattern9]:
		html_char = re.sub(pattern, "", html_char)
	if len(html_char) > 1000:
		return "too_long"
	pattern_html = r"\</*[^\>]*\>"
	decoded_body = re.sub(pattern_html, "", html_char)
	decoded_body = decoded_body.replace(u'\xa0', ' ')
	while "  " in decoded_body or ".." in decoded_body:
		decoded_body = decoded_body.replace("  "," ").replace("..",".")
	return decoded_body


def gmail_get_message(msg_id):
	message = {}
	r = gmail_request("get","messages/{}".format(msg_id))
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
	match = re.search(pattern,From)
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
            if num < 9999 and num > 1000:
                order_name = str(num)
                break
    return order_name
    
    
def detect_irritation_score(message):
    lst1 = ("arnaque","escro","voleur","colere","colère","pas content","mecontent","mécontent","honte","inadmissible","fureur","furie","fache","fâche","rage","inacceptable","inexcusable")
    lst2 = ("plainte","justice","judiciaire","polic","flic","gendarmerie","demeure","avocat","tribunal","services compétents")
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
    
    
def deepl_front(text):

    error = True
    phrases = text.split(".")
    for phrase in phrases:
        if re.search(r"\w+\s\w+\s\w+", phrase):
            r = requests.post("https://api.deepl.com/v2/translate?auth_key=478283b2-3683-820d-9433-2d3c243eb689&target_lang=FR&text={}".format(phrase))
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
        r = requests.post("https://api.deepl.com/v2/translate?auth_key=478283b2-3683-820d-9433-2d3c243eb689&target_lang=FR&text={}".format(text))
        translations = r.json()["translations"]
        translation = translations[0]["text"]
        return source_language, translation
        

def deepl_back(text, target_lang):

    tags = re.findall(r"<[^>]*>", text)
    lines = re.findall(r">([^<]*)<", text)

    phrases = ""
    for line in lines:
        phrases += "&text={}".format(line)
        
    r = requests.post("https://api.deepl.com/v2/translate?auth_key=478283b2-3683-820d-9433-2d3c243eb689&target_lang={}{}".format(target_lang,phrases))
    translations = r.json()["translations"]
    translation_text = []
    for t in translations:
        translation_text.append(t["text"])
    len_t = len(tags)
    len_p = len(translation_text)
    new_text = ""
    for i in range(max(len_t,len_p)):
        if i <= len_t:
            new_text += tags[i]
        if i <= len_p:
            new_text += translation_text[i]
    
    return new_text
    
    
def shopify_date(date):
    date = date[:10]
    lst = date.split("-")
    return datetime(int(lst[0]),int(lst[1]),int(lst[2]))
    
    
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
    
    
def detect_response(questions,message,history):

    response = ["/ALERT Aucun cas de figure detecté"]    #Default
    answer_id = "s0"
    answer_ids = []
    last_answer = False
    global messages_dic_1, messages_dic_2

    for l in history:
        if l[0] == message["email"]:
            if "s" in l[3]:
                last_answer = False
            else:
                last_answer = True
            answer_ids = list(eval(l[3]))
            last_answer_id = answer_ids[-1]
            break
            
    if last_answer:
        for l in messages_dic_2:
            if l[2] == [""]:
                c1 = (questions[0] in l[1]) or (questions[1] in l[1])
            else:
                c1 = ((questions[0] in l[1]) or (questions[0] in l[2])) and ((questions[1] in l[1]) or (questions[1] in l[2]) or (questions[1] == "none"))
            c2 = last_answer_id in l[0] or l[0] == ""
            if c1 and c2:
                response = l[6]
                answer_id = l[8][0]
                break
                
        if response == ["/ALERT Aucun cas de figure detecté"]:
            last_answer = False
    
    if not last_answer:
        for l in  messages_dic_1:
            if l[1] == [""]:
                c1 = (questions[0] in l[0]) or (questions[1] in l[0])
            else:
                c1 = ((questions[0] in l[0]) or (questions[0] in l[1])) and ((questions[1] in l[0]) or (questions[1] in l[1]) or (questions[1] == "none"))
            if c1:
                response = l[6]
                answer_id = l[9][0]
                break
                
    if answer_id in answer_ids:
        return "double", "double"
        
    file = open("history.csv","a")
    file.write("\n{},{},{},{}".format(message["email"],str(datetime.now())[:-7],str(questions).replace(",","$"),str(answer_ids).replace("\r","")))
    file.close()
        
    return response[0], answer_id.replace("\r","")
    
    
def create_mime_msg(sender, message_text, message):
    mime_msg = MIMEText(message_text, "html")
    mime_msg['to'] = message["email"]
    mime_msg['from'] = sender
    mime_msg['subject'] = "Re: {}".format(message["subject"])
    mime_msg['In-Reply-To'] = message["Message_ID"]
    mime_msg["References"] = message["Message_ID"]
    return {'raw':base64.urlsafe_b64encode(mime_msg.as_string().encode()).decode(), "threadId":message["threadId"]}


def build_text_msg(response,answer_id,message,history):

    response2 = response.replace("$",",")
    response2 = response2.replace("{first_name}",message["first_name"])
    
    now = datetime.now()
    if now.hour >= 19:
        hello = "Bonsoir"
        ends = ["Très bonne soirée", "Passez une bonne soirée", "Bien à vous"]
    else:
        ends = ["Très bonne journée", "Passez une bonne journée", "Bien à vous"]
        hello = "Bonjour"
    hello_msg = "{}{},<br><br>".format(hello,message["first_name"])
    
    welcome = "Merci d'avoir contacté notre service client ! Je m'appelle Lucie et suis prête à faire de mon mieux pour satisfaire votre demande :)<br><br>"
    for l in history:
        if l[0] == message["email"]:
            welcome = ""
            if shopify_date(l[1]).date() == now.date():
                hello_msg = ""
            break
        
    if "s" not in answer_id:
        end = ends[random.randint(0,len(ends)-1)]
        signature = "<br><br>{},<br><br>Lucie de l'équipe service client".format(end)
    else:
        signature = "<br><br>Lucie de l'équipe service client"
        
    message_text = "<img src=\"{}\" alt=\"\" />{}{}{}{}<".format("h",hello_msg,welcome,response2,signature)
    if message["source_language"] != "FR":
        message_text = deepl_back(message_text, message["source_language"])
    return message_text
    
    
############################ SCRIPT ###########################


file = open("message_ids.csv","r")
cont_message_ids = file.read()
file.close()
lst_message_ids = cont_message_ids.split("\n")

file = open("liste_prenom_FR_EN.txt","r")
cont2 = file.read()
file.close()
name_list = cont2.split("\n")

while True:
    r = gmail_request("get","messages",endpoints="maxResults=5&q=label:inbox&")
    messages = r.json()["messages"]
    for message in messages:
        message_id = message["id"]
        if message_id not in lst_message_ids:
        
            messages_dic_1,messages_dic_2 = build_messages_dic()
            history = build_history()
            
            message = gmail_get_message(message_id)
            
            if message == {"STARRED"}:
                append_message_id(message_id)
                print("history saved ! waiting for another message\n")
                #raise StarredError("This message is starred !")
                continue
                        
            if message["source_language"] == "ERROR":
                append_message_id(message_id)
                message_text = "I could not identify the client's language"
                mime_msg = create_mime_msg(EMAIL, message_text, message)
                gmail_request("post","drafts",endpoints="", post_data={"message":mime_msg})
                print("history saved ! waiting for another message\n")
                continue
        
            score, menace = detect_irritation_score(message)
            while "!!" in message["data"] or "??" in message["data"]:
                message["data"] = message["data"].replace("!!","!").replace("??","?")
                
            if message["data"] != "too_long":
                message["order_name"] = detect_order_name(message)
                print("new email received :\n{}".format(message))
                questions = detect_question(message["data"],message["subject"])
                print("questions :\n" + str(questions))
                if "thanks" in questions and "status" in questions:
                    questions = ["status","none"]
                if "thanks" in questions and "tracking_PB" in questions:
                    questions = ["tracking_PB","none"]
                    
                response, answer_id = detect_response(questions,message,history)
                
                if menace:
                    response = "/ALERT This customer looks angry !"
                elif score > 70:
                    response = "/ALERT This customer is dangerous because he may file a complaint !"
                elif response != "no reply":
                    if "/ALERT" not in response:
                        message_text = build_text_msg(response,answer_id,message,history)
                        mime_msg = create_mime_msg(EMAIL, message_text, message)
                        gmail_request("post","messages/send",endpoints="", post_data=mime_msg)
                        # gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
    
                    else:
                        message_text = response.replace("/ALERT ","")
                        mime_msg = create_mime_msg(EMAIL, message_text, message)
                        gmail_request("post","drafts",endpoints="", post_data={"message":mime_msg})
                        put_a_star(message)

                    print("response :\n" + str(message_text))
                    
            elif message["data"] == "too_long":
                message_text = "Ce message est trop long, il ne vient peut être pas d'un client."
                mime_msg = create_mime_msg(EMAIL, message_text, message)
                gmail_request("post","drafts",endpoints="", post_data={"message":mime_msg})
                
            append_message_id(message_id)
            print("history saved ! waiting for another message\n")
            
            
    