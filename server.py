import os
from re import S
import flask
from flask import request, session, jsonify, render_template
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from sqlalchemy.exc import NoResultFound
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

import json
from models import db

CLIENT_SECRETS_FILE = "client_secret.json"

SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/calendar.events',
          'https://www.googleapis.com/auth/userinfo.profile',
          'https://www.googleapis.com/auth/calendar']

credentials = None


# get flow
def get_flow():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
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
            credentials = flow.run_local_server(port=8080,
                                                prompt='consent',
                                                authorization_prompt_message="")

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
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://fermovies:@localhost/fermovies'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
from models import Creds


def getuserinfo(username: str):
    try:
        cred: Creds = Creds.query.filter_by(username=username).one()
    except NoResultFound:
        return {'data': None}
    result = {
        'data': True,
        "state": cred.state, "username": cred.username, "chatid": cred.chatId,
        "credentials": {
            "token": cred.token,
            "refresh_token": cred.refresh_token,
            "token_uri": cred.token_uri,
            "client_id": cred.client_id,
            "client_secret": cred.client_secret
        }
    }
    return result


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/setcalender')
def setcalender():
    data = request.get_json()
    username = data['username']
    message = data['message']
    calendarId = data['calendarId']

    response = getuserinfo(username)

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
    return {"htmllink": created_event['htmlLink'], "data": True}


# authorize
@app.route("/sign-in-with-google")
def sign_in_google():
    username = request.args.get("username")
    chatid = request.args.get("chatid")
    data = getuserinfo(username)
    if data['data'] is None:
        # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
        flow = get_flow()

        authorization_url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true"
        )

        # Store the state so the callback can verify the auth server response.
        flask.session["username"] = username
        flask.session["chatid"] = chatid
        flask.session["state"] = state
        return flask.redirect(authorization_url)
    else:
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
    save_credentials(credentials, 'oauth_token.pickle')
    print("This are those who dice you: ", credentials)
    print("=" * 100)
    print(credentials_to_dict(credentials))
    print("=" * 100)

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
    creds = Creds(
        state=state,
        username=username,
        chatId=chatid,
        token=token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret
    )
    db.session.add(creds)
    db.session.commit()
    return f"Done!!"


@app.route('/authorize')
def login():
    username = request.args.get("username")
    chatid = request.args.get("chatid")
    return render_template('index.html',
                           username=username, chatid=chatid)


# This is redirect takes care of updating the database
@app.route('/updatedb')
def updatedb():
    data = request.get_json()
    state = data['state']
    token = data['token']
    refresh_token = data['refresh_token']
    token_uri = data[
        'token_uri']  # ".replace('https://', '').replace('.apps.googleusercontent.com', '')
    client_id = data[
        'client_id']  # .replace('https://', '').replace('.apps.googleusercontent.com', '')
    client_secret = data['client_secret']
    print({"client_id": client_id, "client_secret": client_secret})
    Creds.query.filter_by(state=state).update(
        dict(token=token,
             refresh_token=refresh_token,
             token_uri=token_uri,
             client_id=client_id,
             client_secret=client_secret)
    )
    return {"data": True}


# This is redirect takes care of getting data from the database
@app.route('/getuserinfo')
def getdata():
    data = request.get_json()
    username = data['username']
    result = getuserinfo(username)
    if result['data'] == None:
        print("IF DATA", result)
        return jsonify({"data": None})
    else:
        return jsonify(result)


# This is redirect takes care of getting data from the database
@app.route('/getchatid')
def getchatid():
    data = request.get_json()
    state = data['state']
    try:
        cred: Creds = Creds.query.filter_by(state=state).one()
    except NoResultFound:
        return {'data': None}
    return {"chatid": cred.chatId}


@app.route('/5168649663:AAHe5Qq2wx4y3V_3MQ7ci3klc7ZKkTJ8kQM')
def tgwebhook():
    print(request)
    data = request.get_json()
    print(data)


if __name__ == '__main__':
    app.run(debug=True,
            ssl_context='sasasa', host='localhost')
