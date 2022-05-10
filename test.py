import json
import requests
from gclass import gapi

scrape = gapi(1).mail()
emails = scrape.to_dict('Records')
for i in range(len(emails)):
    reqUrl = "http://127.0.0.1:5000/depositos"

    headersList = {
    "Content-Type": "application/json" 
    }

    payload = json.dumps(emails[i])

    response = requests.request("POST", reqUrl, data=payload,  headers=headersList)

print(response.text)
