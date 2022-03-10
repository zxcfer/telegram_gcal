from __future__ import print_function
import json
from pymongo import MongoClient
from urllib.parse import urlparse
from urllib.parse import parse_qs
from google_auth_oauthlib.flow import Flow
from flask import Flask, request
from time import sleep
import requests
from decouple import config
token = config('TOKEN')
dburl = config('DBURL')
domain = config('DOMAIN')
conn = MongoClient(dburl)
databasename = "myFirstDatabase"
collectionname = "calender"
db = conn.databasename
collection = db.collectionname
app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly','https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/calendar.events']

flow = Flow.from_client_secrets_file(
    'redirecttoken.json',
    scopes=SCOPES,
    redirect_uri=f'{domain}/token')

def add(data):
    dataa = collection.insert_one(data)
    print(dataa)
    return dataa

my_list = []

def find(data):
    for x in collection.find(data):
        my_list.append(x)
    data = my_list[-1];
    return data



def update(myquery, newvalues):
    dataa = collection.update_one(myquery, {"$set":newvalues})
    print(dataa)
    return(dataa)



def delete(query):
        dataa = collection.delete_one(query)
        print(dataa)
        return(dataa)



def main(meta):
    auth_url, _ = flow.authorization_url(prompt='consent')
    parsed_url = urlparse(format(auth_url))
    user_id = parse_qs(parsed_url.query)['state'][0]
    print("============================ break")
    add({"sessionId":user_id, "chatid":meta['chatid'],"username":meta['username']})
    return format(auth_url)

@app.route('/token')
def code():
    tokenn = request.args.get('code')
    sessionId = request.args.get('state')
    t = flow.fetch_token(code=tokenn)
    update({"sessionId": sessionId},t)
    sleep(1)
    print(t)
    user_info = find({"sessionId":sessionId})
    print(user_info['chatid'])
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = json.dumps({
        "chat_id": user_info['chatid'],
        "text": "You've sucessfully connected your google calender, you can now use the /schedule command"
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    print(f'response from telegram botm{response.text}')

    return "Authenticaton flow has been completed, you can close the browser now"


@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run(debug=True, ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0', port=8080)

