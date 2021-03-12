import base64
import apiai
from datetime import datetime, time
from email.mime.text import MIMEText
from test.Gmail_ResquestTest import Shopify


class QuestionTest(Shopify):
    def create_mime_msg(sender, message_text, message):
        mime_msg = MIMEText(message_text, "html")
        mime_msg['to'] = message["email"]
        mime_msg['from'] = sender
        mime_msg['subject'] = "Re: {}".format(message["subject"])
        mime_msg['In-Reply-To'] = message["Message_ID"]
        mime_msg["References"] = message["Message_ID"]
        return {'raw' :base64.urlsafe_b64encode(mime_msg.as_string().encode()).decode(), "threadId" :message["threadId"]}


    def build_text_msg(shop ,response ,answer_id ,message ,order_info ,history):
        global img
        if "time" in order_info.keys():
            time = order_info["time"]
        else:
            time = 400
        if time < 2:
            time_txt = "d'ici quelques jours"
        elif 2 <= time < 7:
            time_txt = "cette semaine"
        elif 7 <= time < 10:
            time_txt = "d'ici une semaine"
        elif 10 <= time:
            time_txt = "sous une dizaine de jours ouvrés"

        response2 = response.replace("$" ,",")
        if "tracking_num" in order_info.keys():
            response2 = response2.replace("{tracking_num}" ,order_info["tracking_num"])
        response2 = response2.replace("{first_name}" ,message["first_name"])
        if "name" in order_info.keys():
            response2 = response2.replace("{order_name}" ,order_info["name"])
        response2 = response2.replace("{time}" ,time_txt)

        now = datetime.now()
        if now.hour >= 19:
            hello = "Bonsoir"
            ends = ["Très bonne soirée", "Passez une bonne soirée", "Bien à vous"]
        else:
            ends = ["Très bonne journée", "Passez une bonne journée", "Bien à vous"]
            hello = "Bonjour"
        hello_msg = "{}{},<br><br>".format(hello ,message["first_name"])

        welcome = "Merci d'avoir contacté notre service client ! Je m'appelle Lucie et suis prête à faire de mon mieux pour satisfaire votre demande :)<br><br>"
        for l in history:
            if l[0] == message["email"]:
                welcome = ""
                if shopify_date(l[1]).date() == now.date():
                    hello_msg = ""
                break

        shop2 = shop
        if shop == None:
            shop2 = "service client"
            shop = "BUFFALO"
        if "s" not in answer_id:
            end = ends[random.randint(0 ,len(ends ) -1)]
            signature = "<br><br>{},<br><br>Lucie de l'équipe {}".format(end ,shop2)
        else:
            signature = "<br><br>Lucie de l'équipe {}".format(shop2)

        message_text = "<img src=\"{}\" alt=\"\" />{}{}{}{}<".format(img[shop] ,hello_msg ,welcome ,response2 ,signature)
        if message["source_language"] != "FR":
            message_text = deepl_back(message_text, message["source_language"]).replace("<" ,"")
        return message_text


    def fb_new(shop ,questions ,order_info ,message ,answer_id ,menace ,score):
        if "modify_adress" in questions and order_info == {}:
            file = open("shops/{}/messages_cache.csv".format(shop) ,"r")
            cont = file.read()
            file.close()
            dic = eval(cont.replace("$" ,","))
            dic[message["email"]] = str(message).replace("," ,"$")
            file = open("shops/{}/messages_cache.csv".format(shop) ,"w")
            file.write(str(dic))
            file.close()

        if menace:
            answer_id = "menace"
            alert_msg = "Attention, je viens de recevoir un message d'un client qui menace de porter plainte !"
        elif score > 70:
            answer_id = "angry"
            alert_msg = "Attention, je viens de recevoir un message d'un client qui semble très en colère !"
        elif answer_id == CANCEL_ID:
            alert_msg = "Un client veut annuler sa commande et celle ci n'a pas encore été traitée."
        elif answer_id == REFUND_ID:
            alert_msg = "Un client demande a être remboursé et n'a pas reçu sa commande depuis plus de 30 jours."
        else:
            alert_msg = ""

        if answer_id in [CANCEL_ID ,REFUND_ID ,ADDRESS_ID ,"menace" ,"angry"]:
            global clients
            for owner in clients.keys():
                if shop in clients[owner]["shops"]:
                    owner2 = owner
                    thread_id = clients[owner]["thread_id"]
                    break
            file = open("clients/{}/messenger_assistant.csv".format(owner2) ,"r")
            cont = file.read()
            file.close()
            session_id = "ID{}".format("".join([str(random.randint(0 ,9)) for i in range(10)]))
            if cont == "":
                ai = apiai.ApiAI("5748c522a6614cd38896b9b704ea6462")
                phrase = "id {}".format(answer_id)
                rep_text, contexts = apiai_request(ai ,phrase ,session_id)
                if order_info != {}:
                    text = build_fb_answer(shop ,order_info ,message ,rep_text ,"").replace("/alert_msg" ,alert_msg)
                else:
                    text = "{} Son message : {} Malheureusement je ne l'ai pas retrouvé dans ta liste de clients. Je te laisse donc voir ça avec lui ! Son mail : {} , envoyé sur {}".format \
                        (alert_msg ,message["data"] ,message["email"] ,shop)
                    fb_send(text ,thread_id)
                    return None

            else:
                text = "Stp répond à mon précédent message, j'aurai d'autres trucs à te dire après ça"
                contexts = []
                cont += "\n"

            fb_send(text ,thread_id)

            actions = {CANCEL_ID :"refund" ,REFUND_ID :"refund" ,ADDRESS_ID :"modify_adress" ,"menace" :"menace"
                       ,"angry" :"angry"}
            action = actions[answer_id]

            if order_info != {}:
                order_info["date"] = str(order_info["date"])
                if order_info["last_tracking_date"] != None:
                    order_info["last_tracking_date"] = str(order_info["last_tracking_date"])
                if order_info["status"] != "not_fulfilled":
                    order_info["fulfillment_date"] = str(order_info["fulfillment_date"])

            file = open("shops/{}/messages_cache.csv".format(shop) ,"r")
            cont2 = file.read()
            file.close()
            dic = eval(cont2.replace("$" ,","))
            if message["email"] in dic.keys():
                message = dic[message["email"]]

            file = open("clients/{}/messenger_assistant.csv".format(owner) ,"w")
            file.write("{}{},{},{},{},{},{}".format(cont ,session_id ,action ,shop ,str(message).replace("," ,"$")
                                                    ,str(order_info).replace("," ,"$") ,str(contexts).replace("," ,"$")))
            file.close()

        return None

    def build_fb_answer(shop ,order_info ,message ,rep_text ,sender):
        global today_msg ,today_nt ,credit
        order_time = str(order_info["order_time"])
        order_name = order_info["name"]
        total_price = str(order_info["total_price"])
        if order_info["status"] == "not_fulfilled":
            tracking = "Cette commande est non traitée sur shopify !"
        else:
            tracking = "La commande a bien été expédiée il y a {} jours, voici son numéro de suivi : {}".format(order_time
                                                                                                                ,order_info
                                                                                                                    ["tracking_num"])
        full_info = "Commande {}, passée il y a {} jours sur votre boutique {} pour un montant total de {}€. {}".format \
            (order_name ,order_time ,shop ,total_price ,tracking)
        answer = rep_text
        answer = answer.replace("/message_name" ,message["full_name"])
        answer = answer.replace("/message_email" ,message["email"])
        answer = answer.replace("/message_data" ,message["data"])
        answer = answer.replace("/order_time" ,order_time)
        answer = answer.replace("/order_name" ,order_name)
        answer = answer.replace("/total_price" ,total_price)
        answer = answer.replace("/tracking" ,tracking)
        answer = answer.replace("/full_info" ,full_info)
        answer = answer.replace("/shop" ,shop)
        answer = answer.replace("/sender" ,sender)
        answer = answer.replace("/today_msg" ,str(today_msg))
        answer = answer.replace("/today_nt" ,str(today_nt))
        answer = answer.replace("/credit" ,str(credit))
        answer = answer.replace("il y a 0 jours" ,"aujourd'hui")
        return answer

