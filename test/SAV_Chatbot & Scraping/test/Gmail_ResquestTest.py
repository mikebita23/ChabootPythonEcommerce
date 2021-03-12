import requests
from datetime import datetime, time


class Shopify(object):
    pass

class QuestionTest(Shopify):
    def gmail_request(shop,req_type,ressource,endpoints="",post_data={}):
        global user_id,api_key,client_id,client_secret,refresh_token,access_tokens
        tries = 0
        #print(shop)
        while tries < 20:
            try:
                cont = "https://www.googleapis.com/gmail/v1/users/{}/{}?{}key={}".format(user_id[shop],ressource,endpoints,api_key[shop])
                if req_type == "get":
                    r = requests.get(cont,headers={"Authorization":"OAuth {}".format(access_tokens[shop])}, timeout=15)
                    #print(r.json())
                elif req_type == "post":
                    r = requests.post(cont,headers={"Authorization":"OAuth {}".format(access_tokens[shop])},json=post_data, timeout=15)
                if r.status_code > 300:
                    data = {"client_id":client_id[shop],"client_secret":client_secret[shop],"refresh_token":refresh_token[shop],"grant_type":"refresh_token"}
                    r2 = requests.post("https://www.googleapis.com/oauth2/v4/token",data=data, timeout=15)
                    #print(r2.json())
                    access_tokens[shop] = r2.json()["access_token"]
                    continue #retry a request with a new access_token
                break
            except:
                print("connexion error on gmail, retrying...")
                time.sleep(10)
                tries += 1
        return r