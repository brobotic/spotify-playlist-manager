import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    CLIENT_ID = os.environ.get('CLIENT_ID') or 'client id goes here'
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET') or 'client secret goes here'
    SPOTIFY_USER = os.environ.get('SPOTIFY_USER') or 'spotify username goes here'
    EMAIL_SMTP = 'smtp.gmail.com'
    EMAIL_PORT = '587'
    EMAIL_SENDER = 'sender@server.com'
    EMAIL_PASSWORD = 'email password goes here'
    EMAIL_RECIPIENTS = ['recipient1@server.com', 'recipient2@server.com']
    REDIRECT_URI = 'http://localhost:8888/callback/'