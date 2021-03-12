import base64
import json


class Shopîfy(object):
    pass


class QuestionTest(Shopîfy):
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