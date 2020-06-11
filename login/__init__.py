# from google.oauth2 import id_token
# from google.auth.transport import requests
from flask_login import login_user
from google.auth.transport import requests
from google.oauth2 import id_token

from login.user import User
from vars import GOOGLE_CLIENT_ID


def check_token(token):
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        # Or, if multiple clients access the backend server:
        # idinfo = id_token.verify_oauth2_token(token, requests.Request())
        # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
        #     raise ValueError('Could not verify audience.')

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # If auth request is from a G Suite domain:
        # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
        #     raise ValueError('Wrong hosted domain.')

        # ID token is valid. Get the user's Google Account ID from the decoded token.

        unique_id = idinfo['sub']
        users_name = idinfo['name']
        users_email = idinfo['email']
        picture = idinfo['picture']

        # user = User(
        #     id_=unique_id, name=users_name, email=users_email, profile_pic=picture
        # )
        if not User.get(unique_id):
            User.create(unique_id, users_name, users_email, picture)

        user = User.get(unique_id)
        login_user(user)
        return users_email
    except ValueError:
        # Invalid token
        pass
