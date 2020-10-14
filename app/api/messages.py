import phonenumbers
import re
import requests
import time
from flask import jsonify, request, url_for, request, current_app
from app import tryton, mail
from app.api import bp
from pymessenger.bot import Bot
from pymessenger import Element, Button

# Make a regular expression
# for validating an Email
regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

MessengerCredential = tryton.pool.get('web.messenger.credential')
Messenger = tryton.pool.get('web.messenger')
Party = tryton.pool.get('party.party')
ContactMechanism = tryton.pool.get('party.contact_mechanism')

def verify_webhook(req):
    if req.args.get("hub.verify_token") == current_app.config['VERIFY_TOKEN']:
        return req.args.get("hub.challenge")
    else:
        return "incorrect"

def is_user_message(message):
    """Check if the message is a message from the user"""
    is_message = message.get('message') and message['message'].get('text')
    is_echo = True
    if message.get('message') and message['message'].get('is_echo'):
        is_echo = message['message']['is_echo']
    return ( is_message and is_echo )

def is_postback_message(message):
    """Check if the message is a postback message from the user"""
    return (message.get('postback') and
        message['postback'].get('title') and
            not message['postback'].get('is_echo'))

def buttons_response(bot, sender, message):
    buttons = []

    for button in message.buttons:
        if button.kind == 'postback':
            item = Button(title=button.name, type=button.kind,
                payload=button.name.lower())
            buttons.append(item)
        if button.kind == 'web_url':
            item = Button(title=button.name, type=button.kind,
                url=button.url)
            buttons.append(item)

    text = message.response
    bot.send_button_message(sender, text, buttons)

def phone_quick_response(bot, sender, message):
    text = message.response
    bot.send_quick_reply(sender, text, "user_phone_number")

def email_quick_response(bot, sender, message):
    text = message.response
    bot.send_quick_reply(sender, text, "user_email")

def valid_email(email):
    if( re.search(regex, email) ):
        return True
    return False

def valid_phone(phone):
    try:
        z = phonenumbers.parse(phone, "GT")
        if phonenumbers.is_valid_number(z):
            return True
    except phonenumbers.NumberParseException:
        print("Invalid phone number")
        return False
    try:
        phone = int(phone)
        if isinstance(phone, int):
            if phone > 30000000 and phone < 99999999:
                return True
            return False
    except ValueError:
        return False

    return False

def get_response_for_email(text, party, credential):
    prev_message = Party.get_prev_message(party)
    if not prev_message:
        return None
    if prev_message.kind == 'quick' and prev_message.quick_type == 'user_email':
        if valid_email(text):
            try:
                Party.create_contact_mechanism(party, 'email', text)
            except:
                pass
            try:
                end_message, = Messenger.search([
                    ('response_type','=','final_message'),
                    ('owner','=',credential.id)],
                    limit=1)
            except:
                print('No end message defined')
                return None
            return end_message
        else:
            try:
                incorrect_email_message, = Messenger.search([
                    ('response_type','=','incorrect_email'),
                    ('owner','=',credential.id)],
                    limit=1)
            except:
                print('No incorrect message defined')
                return None
            return incorrect_email_message
    if prev_message.response_type == 'incorrect_email':
        if valid_email(text):
            try:
                Party.create_contact_mechanism(party, 'email', text)
            except:
                pass
            try:
                end_message, = Messenger.search([
                    ('response_type','=','final_message'),
                    ('owner','=',credential.id)],
                    limit=1)
            except:
                print('No end message defined')
                return None
            return end_message
        else:
            try:
                incorrect_email_message, = Messenger.search([
                    ('response_type','=','incorrect_email'),
                    ('owner','=',credential.id)],
                    limit=1)
            except:
                print('No incorrect message defined')
                return None
            return incorrect_email_message

def get_response_for_phone(text, party, credential):
    prev_message = Party.get_prev_message(party)
    if not prev_message:
        return None
    if prev_message.kind == 'quick' and prev_message.quick_type == 'user_phone_number':
        if valid_phone(text):
            try:
                Party.create_contact_mechanism(party, 'phone', text)
            except:
                pass
            # search for email message to respond
            try:
                email_message, = Messenger.search([
                    ('response_type','=','response_phone'),
                    ('owner','=',credential.id)],
                    limit=1)
            except:
                return None
            return email_message
        else:
            try:
                incorrect_phone, = Messenger.search([
                    ('response_type','=','incorrect_phone'),
                    ('owner','=',credential.id)],
                    limit=1)
            except:
                return None
            return incorrect_phone
    if prev_message.response_type == 'incorrect_phone':
        if valid_phone(text):
            try:
                Party.create_contact_mechanism(party, 'phone', text)
            except:
                pass
            # search for email message to respond
            try:
                email_message, = Messenger.search([
                    ('response_type','=','response_phone'),
                    ('owner','=',credential.id)],
                    limit=1)
            except:
                return None
            return email_message
        else:
            try:
                incorrect_phone, = Messenger.search([
                    ('response_type','=','incorrect_phone'),
                    ('owner','=',credential.id)],
                    limit=1)
            except:
                return None
            return incorrect_phone

    return None

def respond(bot, sender, text, message, credential, party):
    """Formulate a response to the user and
    pass it on to a function that sends it."""

    bot.send_action(sender, 'mark_seen')
    bot.send_action(sender,'typing_on')
    time.sleep(1.5)

    if message.kind == 'simple':
        bot.send_text_message(sender, message.response)
        bot.send_action(sender,'typing_off')
        Party.create_new_message(party, user_message=message,
            bot_message=text)
        if message.next_message:
            respond(bot, sender, text, message.next_message, credential, party)
    elif message.kind == 'button':
        buttons_response(bot, sender, message)
        Party.create_new_message(party, user_message=message,
            bot_message=text)
        bot.send_action(sender,'typing_off')
    elif message.kind == 'quick':
        if message.quick_type == 'user_phone_number':
            phone_quick_response(bot, sender, message)
            Party.create_new_message(party, user_message=message,
                bot_message=text)
            bot.send_action(sender,'typing_off')
        elif message.quick_type == 'user_email':
            email_quick_response(bot, sender, message)
            Party.create_new_message(party, user_message=message,
                bot_message=text)
            bot.send_action(sender,'typing_off')
    elif message.kind == 'attachment_url':
        bot.send_image_url(sender, message.attachment_url)
        Party.create_new_message(party, user_message=message,
                bot_message=text)
        bot.send_action(sender,'typing_off')

    return 'ok'

@bp.route("/webhook", methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def listen():
    """This is the main function flask uses to
    listen at the `/webhook` endpoint"""
    if request.method == 'GET':
        return verify_webhook(request)
    elif request.method == 'POST':
        payload = request.json
        event = payload['entry'][0]['messaging']
        for x in event:
            if is_user_message(x) or is_postback_message(x):
                if x.get('message'):
                    text = x['message']['text']
                elif x.get('postback'):
                    text = x['postback']['title']
                else:
                    return 'incorrect'
                sender_id = x['sender']['id']
                recipient_id = x['recipient']['id']

                try:
                    credential, = MessengerCredential.search(
                        [('identifier','=',recipient_id)], limit=1)
                except ValueError:
                    return 'incorrect'

                user_details_url = "https://graph.facebook.com/v2.6/%s"%sender_id
                user_details_params = {'fields':'first_name,last_name,profile_pic', \
                    'access_token':credential.token}
                user_details = requests.get(user_details_url, user_details_params).json()
                name_tupple = (user_details['first_name'], user_details['last_name'])
                full_name = ' '.join(name_tupple)
                party = Party.check_if_exists(sender_id, full_name)

                message = get_response_for_email(text, party, credential)

                if not message:
                    message = get_response_for_phone(text, party, credential)

                if not message:
                    try:
                        message, = Messenger.search([
                            ('name','ilike','%'+text+'%'),
                            ('owner','=',credential.id)],
                            limit=1)
                    except ValueError:
                        print("i'm not ready to answer that!")
                        return 'incorrect'

                bot = Bot(credential.token)
                respond(bot, sender_id, text, message, credential, party)
        return "ok"
    return 'incorrect'
