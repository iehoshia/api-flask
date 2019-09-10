from datetime import datetime, date
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, session, request

from flask_login import current_user, login_required
from flask_babel import _, get_locale
#from guess_language import guess_language
from app import db, tryton, mail, login
from app.main.forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app.models import User, Post, Notification #, Message
from app.translate import translate
from app.main import bp
from app.main.forms import ContactForm
from flask_mail import Message
from . import functions

TrytonUser = tryton.pool.get('res.user')
Party = tryton.pool.get('party.party')
ContactMechanism = tryton.pool.get('party.contact_mechanism')
Address = tryton.pool.get('party.address')
Opportunity = tryton.pool.get('sale.opportunity')
OpportunityLine = tryton.pool.get('sale.opportunity.line')

@tryton.default_context
def default_context():
    return TrytonUser.get_preferences(context_only=True)

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        #db.session.commit()
        #g.search_form = SearchForm()
    g.locale = str(get_locale())

@bp.route('/perfil', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def edit_profile():
    user = User(current_user)
    form = EditProfileForm()
    if form.validate_on_submit():
        about_me = form.about_me.data
        name = form.name.data
        user.about_me = about_me
        party = user.party.id
        party = Party(party)
        party.name = name
        user.save()
        party.save()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.email.data = user.email
        form.name.data = user.party.name
        form.about_me.data = user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form,user=user)

@bp.errorhandler(404)
@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@tryton.transaction(readonly=False, user=1)
def index():
    form = ContactForm()
    if form.validate_on_submit():

        firstname = form.firstname.data
        email = form.email.data
        phone = form.phone.data
        city = form.city.data
        today = date.today()
        service = form.course.data
        service = int(service)
        product = functions.get_product(service)

        party1, = Party.create([{
            'name': firstname,
            'is_student':False,
            'is_subscriber':False,
            }])

        ContactMechanism.create([{
            'party': party1.id,
            'type': 'email',
            'value': email,
            }])[0]
        ContactMechanism.create([{
            'party': party1.id,
            'type': 'phone',
            'value': phone,
            }])[0]
        address1, = Address.create([{
            'party': party1.id,
            'city': city,
            }])
        opportunity1, = Opportunity.create([{
            'party':party1.id,
            'address':address1.id,
            'description':'Contacto apixela.net: '+ firstname + ' Tel: ' + phone,
            'company':1,
            'start_date':today,
            'conversion_probability':0.5,
            'medio':'Facebook',
            }])
        OpportunityLine.create([{
            'opportunity':opportunity1.id,
            'service':service,
            'product':product,
            'unit':1,
            'quantity':1,
            }])

        session['firstname'] = firstname

        curso = dict(form.course.choices).get(form.course.data)
        body = "Hemos recibido la siguiente informacion: " + \
            "Nombre: "+ firstname + "\n Email: "+ email + " \n Telefono: " + phone + \
            " \n  Ciudad: " + city + " \n  Curso: " + curso

        msg = Message('Contacto APIXela: '+firstname, sender = 'info@apixela.net', recipients = [email, 'info@apixela.net'])
        msg.body = "Contacto Fb Ads " + body
        mail.send(msg)

        return redirect(url_for('main.welcome'))
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('index.html',user=user, form=form)
    return render_template('index.html', form=form)

@bp.errorhandler(404)
def page_not_found(e):
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('404.html',user=user), 404
    return render_template("404.html"), 404

@bp.route('/bienvenido')
@tryton.transaction(readonly=False, user=1)
def welcome(flash_message=None):
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        if 'firstname' in session:
            firstname = session['firstname']
            return render_template('bienvenido.html', firstname=session['firstname'], user=user,flash_message=flash_message)
        return render_template('bienvenido.html', user=user,flash_message=flash_message)
    if 'firstname' in session:
        return render_template('bienvenido.html', firstname=session['firstname'],flash_message=flash_message)
    else:
        return redirect('/')

@bp.route('/cine')
@tryton.transaction(readonly=False, user=1)
def cine():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('cine.html',user=user)
    return render_template('cine.html')

@bp.route('/reparacion')
@tryton.transaction(readonly=False, user=1)
def reparacion():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('reparacion.html',user=user)
    return render_template('reparacion.html')

@bp.route('/ingles')
@tryton.transaction(readonly=False, user=1)
def ingles():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('ingles.html',user=user)
    return render_template('ingles.html')

@bp.route('/powerpivot')
@tryton.transaction(readonly=False, user=1)
def powerpivot():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('powerpivot.html',user=user)
    return render_template('powerpivot.html')

@bp.route('/diseno')
@tryton.transaction(readonly=False, user=1)
def diseno():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('diseno.html',user=user)
    return render_template('diseno.html')

@bp.route('/computacion')
@tryton.transaction(readonly=False, user=1)
def computacion():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('computacion.html',user=user)
    return render_template('computacion.html')

@bp.route('/produccion')
@tryton.transaction(readonly=False, user=1)
def produccion():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('produccion.html',user=user)
    return render_template('produccion.html')

@bp.route('/mikrotik')
@tryton.transaction(readonly=False, user=1)
def mikrotik():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('mikrotik.html',user=user)
    return render_template('mikrotik.html')

@bp.route('/programacion')
@tryton.transaction(readonly=False, user=1)
def programacion():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('programacion.html',user=user)
    return render_template('programacion.html')

@bp.route('/construccion')
@tryton.transaction(readonly=False, user=1)
def construccion():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('construccion.html',user=user)
    return render_template('construccion.html')

@bp.route('/privacidad')
@tryton.transaction(readonly=False, user=1)
def privacidad():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('privacidad.html',user=user)
    return render_template('privacidad.html')

@bp.route('/encuesta')
def encuesta():
    return redirect('https://docs.google.com/forms/d/e/1FAIpQLSdMdS06GNUk1qpX369UvKpo6bjReFOGULkRo3EGr7siSHCLNg/viewform')

@bp.route('/comprar', methods=['GET', 'POST'])
@tryton.transaction(readonly=False, user=1)
def buy():
    return redirect(url_for('course.enroll'))

@bp.route('/registro', methods=['GET'])
@tryton.transaction(readonly=False, user=1)
def register():
    return redirect(url_for('course.enroll'))
