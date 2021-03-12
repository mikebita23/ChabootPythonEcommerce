import re
import string
import json
import apiai
from test.test_helper import TestCase


class QuestionTest(TestCase):

    def detect_question(text, subject):
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
        phrases = re.split("\.|!|\?", text)
        for phrase in phrases:
            # Tests if the phrase contain characters:
            test = False
            for letter in string.ascii_letters:
                if letter in phrase:
                    test = True
            if test == False:
                text = text.replace(phrase, "")
                continue  # Go to next phrase
            intentName = req(phrase)
            if intentName not in intentList:
                questions.append(intentName)
                intentList.append(intentName)
        l = len(questions)
        if l == 0:
            pattern1 = r"Commande #\d{1,20} confirmée"
            pattern2 = r"Une commande #\d{1,20} est en transit"
            patterns = [pattern1, pattern2]
            default_subject = False
            for pattern in patterns:
                if re.search(pattern, subject):
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
            questions = ["Default Fallback Intent", "none"]
        elif l == 1:
            questions.append("none")
        elif l == 3 and "thanks" in questions:
            questions.remove("thanks")
        elif l >= 3:
            for i in range(l - 2):
                del questions[0]

        return questions
