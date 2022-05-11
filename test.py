import json
import requests
from gclass import gapi


def scrape():
    error = None
    try:
        pull = gapi(1).mail()
        emails = pull.to_dict('Records')
        print(emails)

        reqUrl = "http://127.0.0.1:5000/depositos"

        headersList = {
        "Content-Type": "application/json" 
            }

        response = None

        for i in range(len(emails)):
            payload = json.dumps(emails[i])

            response = requests.request("POST", reqUrl, data=payload,  headers=headersList)

        if not response == None:
            print(response.text)
    except Exception as e:
        error = e
    if error is None:
        gapi(1).read(pull)

while True:
    try:
        scrape()
    except:
        print('Volviendo a intentar')
        continue

