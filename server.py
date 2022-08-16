import os
from re import S
import flask
from flask import request, session, jsonify
import requests
from google_auth_oauthlib.flow import InstalledAppFlow

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from flask_mysqldb import MySQL
from decouple import config
from google.auth.transport.requests import Request
import pickle, os

from apiclient.discovery import build



os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
serverdomain = config('DOMAIN')

tgbottoken = config('TOKEN')

import json

CLIENT_SECRETS_FILE = "client_secret.json"

SCOPES = ["https://www.googleapis.com/auth/calendar",
		  "https://www.googleapis.com/auth/calendar.events"]

credentials = None

# get flow
def get_flow():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    return flow


# get credentials
def get_credentials():
    # token.pickle stores the user's credentials from previously successful logins
    if os.path.exists('token.pickle'):
        print('Loading Credentials From File...')
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    # If there are no valid credentials available, then either refresh the token or log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print('Refreshing Access Token...')
            credentials.refresh(Request())
            save_credentials(credentials, 'token.pickle')
        else:
            print('Fetching New Tokens...')
            flow = get_flow()

            # flow.run_local_server(port=8080, prompt='consent', approval_prompt='force', access_type='offline',
            #                       authorization_prompt_message='')
            credentials = flow.run_local_server(port=8080, prompt='consent', authorization_prompt_message="")

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as f:
                print('Saving Credentials for Future Use...')
                pickle.dump(credentials, f)
    return credentials

# save credentials
def save_credentials(credentials, file_name):
    with open(file_name, 'wb') as token:
        pickle.dump(credentials, token)



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
  print(session)
  return "Welcome to Calender Tg"


@app.route('/setcalender')
def setcalender():
  data = request.get_json()
  username = data['username']
  message = data['message']
  calendarId = data['calendarId']

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
      calendarId=calendarId,
      text=message).execute()
  print(created_event)
  return {"htmllink":created_event['htmlLink'],"data":True}

# authorize
@app.route("/authorize")
def authorize():
    username = request.args.get("username")
    chatid = request.args.get("chatid")
    url = f"{serverdomain}/getuserinfo"

    payload = json.dumps({"username": username})
    headers = {"Content-Type": "application/json"}

    session = requests.Session()
    session.verify = False

    response = session.get(url, headers=headers, data=payload).json()

    if response["data"]==None:
        # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
        flow = get_flow()

        flow.redirect_uri = flask.url_for("oauth2callback", _external=True)

        authorization_url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true"
        )

        # Store the state so the callback can verify the auth server response.
        print(state)
        flask.session["username"] = username
        flask.session["chatid"] = chatid
        flask.session["state"] = state
        return flask.redirect(authorization_url)
    else:
        print("Already Authorized")
        return "This user is already authorized!"


@app.route('/oauth2callback')
def oauth2callback():
    state = flask.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)
    
    credentials = flow.credentials
    save_credentials(credentials,'oauth_token.pickle')
    print("This are those who dice you: ",credentials)
    print("="*100)
    print(credentials_to_dict(credentials))
    print("="*100)

    url = f"{serverdomain}/addtodb"
    
    payload = json.dumps({
        "credentials": credentials_to_dict(credentials),
        "state": state,
        "username": flask.session['username'],
        "chatid": flask.session['chatid']
    })
    headers = {
        'Content-Type': 'application/json'
    }
    
    session = requests.Session()
    session.verify = False
    
    response = session.get(url, headers=headers, data=payload)
    
    print(response)
    
    return flask.redirect(f"{serverdomain}/")


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}


@app.route('/getcals')
def get_calendar_list():
    credentials = pickle.load(open("oauth_token.pickle", "rb"))
    service = build("calendar", "v3", credentials=credentials)
    result = service.calendarList().list().execute()
    return result


# This is redirect takes care of saving data to the database
@app.route('/addtodb')
def addtodb():
    data = request.get_json()
    state = data['state']
    username = data['username']
    chatid = data['chatid']
    token = data['credentials']['token']
    refresh_token = data['credentials']['refresh_token']
    token_uri = data['credentials']['token_uri']
    client_id = data['credentials']['client_id']
    client_secret = data['credentials']['client_secret']
    cursor = mysql.connection.cursor()
    cursor.execute(f''' INSERT INTO {db_table} VALUES(%s,%s,%s,%s,%s,%s,%s,%s)''', (state, username, chatid, token, refresh_token, token_uri, client_id, client_secret)),
    mysql.connection.commit()
    cursor.close()
    return f"Done!!"


@app.route('/createtable')
def createtable():
    cursor = mysql.connection.cursor()
    cursor.execute(f'''CREATE TABLE `{db_table}` ( `state` VARCHAR(1000) NULL , `username` VARCHAR(1000) NULL , `chatId` VARCHAR(1000) NULL , `token` VARCHAR(1000) NULL , `refresh_token` VARCHAR(1000) NULL , `token_uri` VARCHAR(1000) NULL , `client_id` VARCHAR(1000) NULL , `client_secret` VARCHAR(1000) NULL) ENGINE = InnoDB;''')
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
        print("IF DATA", data)
        return jsonify({"data":None})
    else:
        result = {"data":True,"state":data[0], "username":data[1],"chatid":data[2],"credentials":{

                   "token":data[3],
                   "refresh_token":data[4],
                   "token_uri":data[5],
                   "client_id":data[6],
                   "client_secret":data[7]
                }
        }
        print("ELSE res", result)
        return jsonify(result)

# This is redirect takes care of getting data from the database
@app.route('/getchatid')
def getchatid():
    data = request.get_json()
    state = data['state']
    cursor = mysql.connection.cursor()
    cursor.execute(f'SELECT * FROM {db_table} WHERE state = "{state}"')
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
    app.run(debug=True, ssl_context=('cert.pem', 'key.pem'), host='scheduler.f21.app', port=8080)
