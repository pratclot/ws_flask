import json
import logging
import sqlite3

import geventwebsocket
from flask import Flask, redirect, request, url_for, jsonify
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_sockets import Sockets
from gevent import time
from geventwebsocket.websocket import WebSocket
from oauthlib.oauth2 import WebApplicationClient
from pip._vendor import requests

from login import check_token
from login.db import init_db_command, close_db
from login.user import User
from producer import producer, act_on_heater
from tools import frange, get_google_provider_cfg
from vars import SLEEP_TIMEOUT, SLEEP_STEP, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, CONTROL_ENDPOINTS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

login_manager = LoginManager()
login_manager.init_app(app)

app.logger = logging.getLogger("gunicorn.error")
sockets = Sockets(app)


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


try:
    # init_db_command()
    init_app(app)
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

oauth_client = WebApplicationClient(GOOGLE_CLIENT_ID)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route(f"/api{CONTROL_ENDPOINTS['turn_heater_on']}")
def turn_heater_on():
    client_token = request.environ["HTTP_AUTHORIZATION"].split()[1]
    client_id = check_token(client_token)

    app.logger.info(current_user.role)
    if current_user.role != "2":
        response = f"Client {client_id} does not have write permissions!"
        app.logger.info(response)
        return jsonify(response), 403
    else:
        print(f'Turning the heater on for {client_id}')
        return act_on_heater(CONTROL_ENDPOINTS['turn_heater_on'])


@app.route(f"/api{CONTROL_ENDPOINTS['turn_heater_off']}")
def turn_heater_off():
    client_token = request.environ["HTTP_AUTHORIZATION"].split()[1]
    client_id = check_token(client_token)

    if current_user.role != "2":
        response = f"Client {client_id} does not have write permissions!"
        app.logger.info(response)
        return jsonify(response), 403
    else:
        print(f'Turning the heater off for {client_id}')
        return act_on_heater(CONTROL_ENDPOINTS['turn_heater_off'])


@login_required
@sockets.route("/api")
def ranch_socket(ws: WebSocket):
    client_token = ws.environ["HTTP_AUTHORIZATION"].split()[1]
    client_id = check_token(client_token)

    # client_id = ":".join((ws.environ["REMOTE_ADDR"], ws.environ["REMOTE_PORT"]))
    app.logger.info(f"Client came: {client_id}")

    if current_user.is_authenticated:
        if current_user.role == "0":
            response = f"Client {client_id} does not have read permissions!"
            app.logger.info(response)
            return jsonify(response), 403
        else:
            while not ws.closed:
                message = producer()
                app.logger.info(f"Sending {message} to {client_id}")
                if message is None:
                    app.logger.info("Message from backend was None!")
                    continue

                clients = ws.handler.server.clients.values()
                try:
                    for client in clients:
                        client.ws.send(message)
                except geventwebsocket.exceptions.WebSocketError:
                    app.logger.info(f"Client {client_id} disappeared")
                    ws.close()

                for i in frange(0, SLEEP_TIMEOUT, SLEEP_STEP):
                    time.sleep(SLEEP_STEP)
    else:
        response = f"Client {client_id} is not authenticated!"
        app.logger.info(response)
        # return redirect(url_for("login"))
        return jsonify(response), 401


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = oauth_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = oauth_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    oauth_client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = oauth_client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    # Create a user in your db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@login_required
@app.route('/')
def index():
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'


if __name__ == '__main__':
    print("Run with: gunicorn -b 127.0.0.1:8080 -k flask_sockets.worker app:app")
