from datetime import datetime, date
import datetime
from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user

from flask_babel import _, lazy_gettext as _l
from flask_mail import Message

from app import db, tryton, login, mail
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm, \
    CompleteRegistrationForm
from app.auth.oauth import OAuthSignIn
from app.models import User
from app.auth.email import send_password_reset_email
from . import functions
import random
import string

Party = tryton.pool.get('party.party')
ContactMechanism = tryton.pool.get('party.contact_mechanism')
Address = tryton.pool.get('party.address')
Opportunity = tryton.pool.get('sale.opportunity')
OpportunityLine = tryton.pool.get('sale.opportunity.line')

@tryton.default_context
def default_context():
    return User.get_preferences(context_only=True)

def randomStringwithDigitsAndSymbols(stringLength=10):
    """Generate a random string of letters, digits and special characters """
    password_characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(password_characters) for i in range(stringLength))

@bp.route('/login', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def login():
    if 'next' in request.args:
        session['next'] = request.args['next']
    if current_user.is_authenticated:
        if 'next' in session:
            return redirect(session['next'])
        return redirect(url_for('course.index'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.username.data
        password = form.password.data
        user = User.authenticate(email,password)
        if user is not None:
            user = User(user)
        else:
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))
        key = User(user.id).new_session()
        #login_user(user, remember=form.remember_me.data)
        login_user(user, remember=True)
        next_page = url_for('auth.complete')
        return redirect(next_page)
    if 'next' in session:
        return render_template('auth/login.html',title=_('Sign In'),form=form,next=session['next'])
    return render_template('auth/login.html', title=_('Sign In'), form=form)


@bp.route('/logout')
def logout():
    session.pop('next', None)
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def register():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        if user.party.city and user.party.phone:
            if 'next' in session:
                return redirect(session['next'])
            return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = str(form.email.data)
        phone = form.phone.data
        city = form.city.data
        password = form.password.data
        service = form.course.data
        today = date.today()
        service = int(service)
        product = functions.get_product(service)

        party, = Party.create([{
            'name':username,
            'is_subscriber':False,
            'is_student':False,
            }])
        user, = User.create([
                {'email':email,
                'password':password,
                'party':party.id,
                }]
            )
        #user.party = party
        #user.save()
        User.validate_email([user])
        ContactMechanism.create([{
            'party': party.id,
            'type': 'phone',
            'value': phone,
            }])
        address, = Address.create([{
            'party': party.id,
            'city': city,
            }])

        opportunity, = Opportunity.create([{
            'party':party.id,
            'address':address.id,
            'description':'Contacto apixela.net: '+ party.name + ' Tel: ' + phone,
            'company':1,
            'start_date':today,
            'conversion_probability':0.5,
            'medio':'Facebook',
            }])
        OpportunityLine.create([{
            'opportunity':opportunity.id,
            'service':service,
            'product':product,
            'unit':1,
            'quantity':1,
            }])

        curso = dict(form.course.choices).get(form.course.data)
        body = "Hemos recibido la siguiente informacion: " + \
            "Nombre: "+ party.name + "\n Email: "+ email + " \n Telefono: " + phone + \
            " \n  Ciudad: " + city + " \n  Curso: " + curso

        msg = Message('Contacto APIXela: '+party.name, sender = 'info@apixela.net', recipients = [email, 'info@apixela.net'])
        msg.body = "Contacto Fb Ads " + body
        mail.send(msg)

        #flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title=_('Register'),
                           form=form)

@bp.route('/complete', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def complete(next=None):
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        if user.party.city and user.party.phone:
            if 'next' in request.args:
                return redirect(request.args['next'])
            return redirect(url_for('course.index'))
        else:
            form = CompleteRegistrationForm()
            if form.validate_on_submit():
                phone = form.phone.data
                city = form.city.data
                today = date.today()
                service = form.course.data
                service = int(service)
                product = functions.get_product(service)

                party = user.party
                ContactMechanism.create([{
                    'party': party.id,
                    'type': 'phone',
                    'value': phone,
                    }])
                address, = Address.create([{
                    'party': party.id,
                    'city': city,
                    }])

                opportunity, = Opportunity.create([{
                    'party':party.id,
                    'address':address.id,
                    'description':'Contacto apixela.net: '+ party.name + ' Tel: ' + phone,
                    'company':1,
                    'start_date':today,
                    'conversion_probability':0.5,
                    'medio':'Facebook',
                    }])
                OpportunityLine.create([{
                    'opportunity':opportunity.id,
                    'service':service,
                    'product':product,
                    'unit':1,
                    'quantity':1,
                    }])

                curso = dict(form.course.choices).get(form.course.data)
                body = "Hemos recibido la siguiente informacion: " + \
                    "Nombre: "+ party.name + "\n Email: "+ party.email + " \n Telefono: " + phone + \
                    " \n  Ciudad: " + city + " \n  Curso: " + curso

                msg = Message('Contacto APIXela: '+party.name, sender = 'info@apixela.net', recipients = ['info@apixela.net'])
                msg.body = "Contacto Fb Ads " + body
                mail.send(msg)
                flash(_('Congratulations, you are now a finished the register!'))
                if 'next' in request.args:
                    return redirect(request.args['next'])
                return redirect(url_for('auth.login'))
            return render_template('auth/complete.html', title=_('Complete Register'),
                               form=form, user=user)
    else:
        return redirect(url_for('auth.login'))


@bp.route('/reset_password_request', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.search([('email','=',str(form.email.data))])
        if user:
            User.reset_password(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title=_('Reset Password'), form=form)


@bp.route('/reset_password', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    token = request.args.get('token')
    email = request.args.get('email')
    form = ResetPasswordForm()
    if form.validate_on_submit():
        User.set_password_token(email, token, form.password.data)
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

@bp.route('/validate_email', methods=['GET','POST'])
@tryton.transaction(readonly=False,user=1)
def validate_email_token():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    token = request.args.get('token')
    user = User.validate_email_token([token])
    if not user:
        flash(_('Your email has not been validated'))
    else:
        flash(_('Your email has been validated'))
    return render_template('auth/validated_email.html')

@bp.route('/authorize/<provider>')
def oauth_authorize(provider):
    next = None
    if 'next' in request.args:
        next = request.args['next']
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize(next=next)

@bp.route('/callback/<provider>')
@tryton.transaction(readonly=False,user=1)
def oauth_callback(provider):
    oauth = OAuthSignIn.get_provider(provider)
    social_id, name, email, picture = oauth.callback()
    if picture is not None:
        picture = picture['data']['url']
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('auth.login'))
    user = User.search([('email','=',email)])
    if len(user)==1:
        user, = user
        login_user(user, True)
        if user.party.phone and user.party.city:
            user.picture_profile = picture
            user.save()
            if 'state' in request.args:
                return redirect(request.args['state'])
            return redirect(url_for('course.index'))
        else:
            if 'state' in request.args:
                return redirect(url_for('auth.complete',next=request.args['state']))
            return redirect(url_for('auth.complete'))
    else:
        password =  randomStringwithDigitsAndSymbols(10)
        party, = Party.create([{
            'name':name,
            'is_student':False,
            'is_subscriber':False,
            }])
        user, = User.create([{
                'social_id':social_id,
                'picture_profile':picture,
                'email':email,
                'password':password,
                'email_valid':True,
                'party':party.id
                }])
        #user.party = party
        #user.save()
        login_user(user, True)
        if 'state' in request.args:
            return redirect(url_for('auth.complete', next=request.args['state']))
        return redirect(url_for('auth.complete'))
    return redirect(url_for('course.index'),user=user)