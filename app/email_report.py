import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from jinja2 import Environment, PackageLoader
from config import Config

env = Environment(loader=PackageLoader('app', 'templates'))
template = env.get_template('email.html')
template_recommendations = env.get_template('recommendations.html')

def send_email(user, pwd, recipient, subject, html):
    msg = MIMEMultipart('alternative')
    msg['To'] = ', '.join(recipient)
    msg['From'] = Config.EMAIL_SENDER
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))

    '''
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    '''
    try:
        server = smtplib.SMTP(Config.EMAIL_SMTP, Config.EMAIL_PORT)
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(Config.EMAIL_SENDER, recipient, msg.as_string())
        server.close()
        print('successfully sent the mail')
    except Exception as e:
        print("failed to send mail")
        print(e)

def send_report(tracklist, history):
    tmp = template.render(tracks=tracklist, previous_entries=history)
    send_email(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD, Config.EMAIL_RECIPIENTS, 'New Spotify Releases', tmp)

def send_recommendation_report(recs, history):
    tmpl_recs = template_recommendations.render(recommendations=recs, previous_entries=history)
    send_email(Config.EMAIL_SENDER), Config.EMAIL_PASSWORD, Config.EMAIL_RECIPIENTS, 'Recommendations', tmpl_recs)
