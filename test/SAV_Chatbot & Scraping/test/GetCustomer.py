
from Apiai_reqTest import Shopîfy
from UpdateOrder import shopify_request


def shopify_date(param):
    pass


def update_order_ids(shop):
    pass


class QuestionTest(Shopîfy):
    def shopify_get_customer(shop ,message ,history):
        customer_id = "not found"  # Default
        # First try : If the customer id is already in the history
        for l in history:
            if l[0] == message["email"] and l[2] != "no":
                return l[2]

        # Second try : Query in the shopify data
        for query in [message["email"] ,message["full_name"]]:
            r1 = shopify_request(shop ,"get" ,"customers/search.json" ,"?query={}".format(query))
            customers = r1.json()["customers"]
            if customers != [] and len(customers) == 1:
                customer_id = customers[0]["id"]
                break
        return str(customer_id)


    def shopify_get_orders(shop ,message ,customer_id):

        if message["order_name"] != "not found":
            order_id = "not found"
            k = ""
            while k != "stop":

                file = open("shops/{}/order_ids.csv".format(shop) ,"r")
                order_ids = file.read()
                file.close()
                lst = order_ids.split("\n")
                if lst == []:
                    update_order_ids(shop)
                    continue
                for i in lst:
                    lst2 = i.split(",")
                    if lst2[0] == message["order_name"]:
                        order_id = lst2[1]
                        k = "stop"
                if order_id == "not found":
                    update_order_ids(shop)
                    order_id == "new test"
                    continue
                if order_id == "new test":
                    return {}
            r = shopify_request(shop ,"get" ,"orders/{}.json".format(order_id)
                                ,"?status=any&fields=total_price,fulfillments,created_at,name,customer")
            data = r.json()["order"]
        elif customer_id != "not found":
            r = shopify_request(shop ,"get" ,"customers/{}/orders.json".format(customer_id), "?status=any&fields=id,total_price,fulfillments,created_at,name,customer")

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


    def buffalo(shops, message, history, shopify_api_url=None):
        for l in history:
            if l[0] == message["email"] and l[2] != "no":
                customer_id = l[2]
                shop = l[5]
                return shop, customer_id
        for shop in shops:
            if shopify_api_url[shop] != "none":
                customer_id = shops.shopify_get_customer(shop, message, history)
                if customer_id != "not found":
                    return shop, customer_id
        return None, None
