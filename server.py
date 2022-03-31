# -*- coding: utf-8 -*-

import os
import flask
from flask import request
import requests
import datetime
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from flask_mysqldb import MySQL
from decouple import config
serverdomain = config('DOMAIN')

tgbottoken = config('TOKEN')

import json

CLIENT_SECRETS_FILE = "client_secret.json"

SCOPES = ["https://www.googleapis.com/auth/calendar","https://www.googleapis.com/auth/calendar.readonly","https://www.googleapis.com/auth/calendar.events"]

app = flask.Flask(__name__)

app.secret_key = '-=2=skdksmms xnskwow-w=0reolz>/}W{W:SLW:<SJJEKEPP\eeddeeew'
app.config['MYSQL_HOST'] = config('mysqlhost')
app.config['MYSQL_USER'] = config('mysqluser')
app.config['MYSQL_PASSWORD'] = config('mysqlpassword')
app.config['MYSQL_DB'] = config('mysqldb')

db_table = config('mysqltable')

mysql = MySQL(app)

@app.route('/')
def index():
  return "Welcome to Calender Tg"


@app.route('/setcalender')
def setcalender():
  data = request.get_json()
  username = data['username']
  message = data['message']

  url = f"{serverdomain}/getuserinfo"

  payload = json.dumps({
      "username": username
  })
  headers = {
      'Content-Type': 'application/json'
  }
  
  session = requests.Session()
  session.verify = False
  
  response = session.get(url, headers=headers, data=payload).json()

  tcred = {
      "token": response['credentials']['token'],
      "refresh_token": response['credentials']['refresh_token'],
      "token_uri": response['credentials']['token_uri'],
      "client_id": response['credentials']['client_id'],
      "client_secret": response['credentials']['client_secret'],
      "scopes": SCOPES
  }

  credentials = google.oauth2.credentials.Credentials(
      **tcred)
  service = googleapiclient.discovery.build(
      'calendar', 'v3', credentials=credentials)

  created_event = service.events().quickAdd(
      calendarId='primary',
      text=message).execute()
  print(created_event)
  return {"htmllink":created_event['htmlLink'],"data":True}


@app.route('/authorize')
def authorize():
  username = request.args.get('username')
  chatid = request.args.get('chatid')

  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  authorization_url, state = flow.authorization_url(
      access_type='offline',
      include_granted_scopes='true')

  # Store the state so the callback can verify the auth server response.
  print(state)
  flask.session['state'] = state

  url = f"{serverdomain}/addtodb"

  payload = json.dumps({
      "state": state,
      "username": username,
      "chatid": chatid
  })
  headers = {
      'Content-Type': 'application/json'
  }

  session = requests.Session()
  session.verify = False
  
  response = session.get(url, headers=headers, data=payload)

  print(response)

  return flask.redirect(authorization_url)



@app.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = flask.session['state']
  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = flask.request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  credentials = flow.credentials
  credentials = credentials_to_dict(credentials)
  token = credentials['token']
  refresh_token = credentials['refresh_token']
  token_uri = credentials['token_uri']
  client_id = credentials['client_id']
  client_secret = credentials['client_secret']
  scopes0 = credentials['scopes'][0]
  scopes1 = credentials['scopes'][1]
  scopes2 = credentials['scopes'][2]

  url = f"{serverdomain}/updatedb"
  payload = json.dumps({
      "state": state,
      "token":token,
      "refresh_token":refresh_token,
      "token_uri":token_uri,
      "client_id":client_id,
      "client_secret":client_secret,
      "scopes0":scopes0,
      "scopes1":scopes1,
      "scopes2":scopes2
  })
  headers = {
      'Content-Type': 'application/json'
  }
  
  session = requests.Session()
  session.verify = False

  response = session.get(url, headers=headers, data=payload).json()
  print(response)

  url = f"{serverdomain}/getchatid"

  payload = json.dumps({
      "state": state
  })
  headers = {
      'Content-Type': 'application/json'
  }
  response = requests.request("GET", url, headers=headers, data=payload).json()
  print(response)

  url = f"https://api.telegram.org/bot{tgbottoken}/sendMessage"

  payload = json.dumps({
      "chat_id": response['chatid'],
      "text": "You've sucessfully connected your google calender, you can now use the /schedule command"
  })
  headers = {
      'Content-Type': 'application/json'
  }
  response = requests.request("GET", url, headers=headers, data=payload)
  print(f'response from telegram bot {response.text}')
  return "Authenticaton flow has been completed, you can close the browser now"



def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}


# This is redirect takes care of saving data to the database
@app.route('/addtodb')
def addtodb():
    data = request.get_json()
    state = data['state']
    username = data['username']
    chatid = data['chatid']
    cursor = mysql.connection.cursor()
    cursor.execute(f''' INSERT INTO {db_table} VALUES(%s,%s,%s,%s,%s,%s,%s,%s)''', (state, username, chatid,None,None,None,None,None)),
    mysql.connection.commit()
    cursor.close()
    return f"Done!!"


@app.route('/createtable')
def createtable():
    cursor = mysql.connection.cursor()
    cursor.execute(f'''CREATE TABLE `calender_db`.`userinfo` ( `state` VARCHAR(1000) NULL , `username` VARCHAR(1000) NULL , `chatId` VARCHAR(1000) NULL , `token` VARCHAR(1000) NULL , `refresh_token` VARCHAR(1000) NULL , `token_uri` VARCHAR(1000) NULL , `client_id` VARCHAR(1000) NULL , `client_secret` VARCHAR(1000) NULL) ENGINE = InnoDB;''')
    mysql.connection.commit()
    cursor.close()
    return "The database was created Sucessfully"



# This is redirect takes care of updating the database
@app.route('/updatedb')
def updatedb():
    data = request.get_json()
    state = data['state']
    token = data['token']
    refresh_token = data['refresh_token']
    token_uri = data['token_uri']#".replace('https://', '').replace('.apps.googleusercontent.com', '')
    client_id = data['client_id']#.replace('https://', '').replace('.apps.googleusercontent.com', '')
    client_secret = data['client_secret']
    print({"client_id":client_id,"client_secret":client_secret})


    cursor = mysql.connection.cursor()


    cursor.execute(f'''UPDATE `{db_table}` SET `token`="{token}",`refresh_token`="{refresh_token}",`token_uri`= "{token_uri}",`client_id`= "{client_id}",`client_secret`= "{client_secret}" WHERE `state` = "{state}"''')

    mysql.connection.commit()
    cursor.close()
    return {"data":True}

# This is redirect takes care of getting data from the database
@app.route('/getuserinfo')
def getdata():
    data = request.get_json()
    username = data['username']
    cursor = mysql.connection.cursor()
    cursor.execute(f'''SELECT * FROM {db_table} WHERE username = "{username}"''')
    data = cursor.fetchone()
    if data == None:
        return {"data":None}
    else:
        result = {"data":True,"state":data[0], "username":data[1],"chatid":data[2],"credentials":{

                   "token":data[3],
                   "refresh_token":data[4],
                   "token_uri":data[5],
                   "client_id":data[6],
                   "client_secret":data[7]
                }
        }
        return result

# This is redirect takes care of getting data from the database
@app.route('/getchatid')
def getchatid():
    data = request.get_json()
    state = data['state']
    cursor = mysql.connection.cursor()
    cursor.execute(f'''SELECT * FROM {db_table} WHERE state = "{state}"''')
    data = cursor.fetchone()
    if data == None:
        return {"data":None}
    else:
        result = {"chatid":data[2]}
        return result

@app.route('/5168649663:AAHe5Qq2wx4y3V_3MQ7ci3klc7ZKkTJ8kQM')
def tgwebhook():
    print(request)
    data = request.get_json()
    print(data)

if __name__ == '__main__':
    app.run(debug=True, ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0', port=8080)
