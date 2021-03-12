
import requests

from test.Gmail_ResquestTest import Shopify


class QuestionTest(Shopify):
    def shopify_request(shop,req_type,ressource,endpoints="",put_data={}):
        global shopify_api_url
        if req_type == "get":
            r = requests.get("{}/{}{}".format(shopify_api_url[shop],ressource,endpoints), timeout=25)
        elif req_type == "post":
            r = requests.post("{}/{}{}".format(shopify_api_url[shop],ressource,endpoints), json = put_data, timeout=15)
        if req_type == "put":
            r = requests.put("{}/{}{}".format(shopify_api_url[shop],ressource,endpoints), json = put_data, timeout=15)
        return r