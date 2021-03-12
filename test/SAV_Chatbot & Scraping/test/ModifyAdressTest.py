from typing import re
from UpdateOrder import shopify_request
from WebEnginePageTest import gmail_request
from test.Gmail_ResquestTest import Shopify


def unidecode(param):
    pass


def sav_mail(args):
    pass


def create_mime_msg(param, message_text, message):
    pass


class QuestionTest(Shopify):



    def shopify_modify_address(shop, contexts, order_id, lst_zip_codes=None):
        for context in contexts:
            if context["name"] == "modify_adress-followup":
                if "parameters" in context.keys():
                    parameters = context["parameters"]
                    break
                else:
                    return False

        r = shopify_request(shop ,"get" ,"orders/{}.json".format(order_id) ,"?status=any&fields=shipping_address")
        address = r.json()["order"]["shipping_address"]
        if "address" in parameters.keys():
            address["address1"] = parameters["address"]
            address["address2"] = ""
        elif "number" in parameters.keys():
            number = "{} ".format(parameters["number"])
            old = " {}".format(address["address1"])
            address["address1"] = re.sub(r"\D\d+\D", number, old)
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
                if zip[1] == unidecode(geo_city.upper().replace("-" ," ").replace("'" ," ")):
                    address["city"] = geo_city
                    address["zip"] = zip[0]
                    break

        put_data = {"order" :{"id" :order_id, "shipping_address" :address}}
        shopify_request(shop ,"put" ,"orders/{}.json".format(order_id) ,put_data=put_data)
        return True

    def shopify_refund(shop ,order_id):
        r = shopify_request(shop ,"get" ,"orders/{}.json".format(order_id) ,"?status=any&fields=line_items")
        line_items = r.json()["order"]["line_items"]
        line_items_2 = []
        for item in line_items:
            line_item_id = item["id"]
            quantity = item["quantity"]
            line_items_2.append({"line_item_id" :line_item_id, "quantity" :quantity, "restock_type" :"no_restock"})
        put_data = {"refund" :{"currency" :"EUR" ,"shipping" :{"full_refund" :True} ,"refund_line_items" :line_items_2}}
        r2 = shopify_request(shop ,"post" ,"orders/{}/refunds/calculate.json".format(order_id) ,put_data=put_data)
        transactions = r2.json()["refund"]["transactions"]
        transactions_2 = []
        for transaction in transactions:
            del transaction["order_id"]
            del transaction["maximum_refundable"]
            transaction["currency"] = "EUR"
            transaction["kind"] = "refund"
            transactions_2.append(transaction)
        put_data = {"refund" :{"currency" :"EUR" ,"notify" :True ,"shipping" :{"full_refund" :True}
                               ,"refund_line_items" :line_items_2 ,"transactions" :transactions_2}}
        r3 = shopify_request(shop ,"post" ,"orders/{}/refunds.json".format(order_id) ,put_data=put_data)

    def do_action(shop ,owner ,action ,contexts ,order_info ,message):
        global clients
        today_msg = clients[owner]["today_msg"]
        today_nt = clients[owner]["today_nt"]
        credit = clients[owner]["credit"]

        file = open("clients/{}/messenger_cache.txt".format(owner) ,"r")
        lst = eval(file.read())[message["email"]]
        mime_msg = lst[0]
        is_draft = lst[1]
        file.close()

        send = False
        if action == "modify_adress":
            send = shop.shopify_modify_address(shop, contexts, order_info["order_id"])
        elif action == "angry" or action == "menace":
            for context in contexts:
                if context["name"] == "refund":
                    shop.shopify_refund(shop, order_info["order_id"])
                    if is_draft:
                        message_text = "J'ai remboursé intégralement ce client"
                        mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                        gmail_request(shop ,"post" ,"drafts" ,endpoints="", post_data={"message" :mime_msg})
                if context["name"] == "send":
                    send = True
                elif context["name"] == "draft":
                    message_text = "Ce client semblait en colère, tu m'as demandé de ne pas traiter son message"
                    mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                    gmail_request(shop ,"post" ,"drafts" ,endpoints="", post_data={"message" :mime_msg})
                    today_nt += 1
                    return None
        elif action == "refund":
            for context in contexts:
                if context["name"] == "refund":
                    send = True
                    shop.shopify_refund(shop, order_info["order_id"])
                elif context["name"] == "draft":
                    message_text = "Je pensais rembourser ce client mais tu m'as demandé de ne pas traiter son message"
                    mime_msg = create_mime_msg(sav_mail[shop], message_text, message)
                    gmail_request(shop ,"post" ,"drafts" ,endpoints="", post_data={"message" :mime_msg})
                    today_nt += 1
                    return None
        if send:
            if not is_draft:
                gmail_request(shop ,"post" ,"messages/send" ,endpoints="", post_data=mime_msg)
                # gmail_request(shop,"post","drafts",endpoints="", post_data={"message":mime_msg})
            else:
                gmail_request(shop ,"post" ,"drafts" ,endpoints="", post_data={"message" :mime_msg})

        # update_clients_dic(clients,owner,today_msg+1,today_nt,credit-1)
