import requests
from datetime import datetime, date
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, session, request

from flask_login import current_user, login_required
from flask_babel import _, get_locale
#from guess_language import guess_language
from app import db, tryton, mail, login
from app.main.forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app.models import User, Post, Notification, Subscription #, Message
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
WebsiteFirstpage = tryton.pool.get('website.firstpage')
WebsiteCourseFirstPage = tryton.pool.get('website.course.firstpage')

@tryton.default_context
def default_context():
    return TrytonUser.get_preferences(context_only=True)

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
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
    firstpage, = WebsiteFirstpage.search([], limit=1,
        order=[('date','DESC'),
        ('id','DESC')])
    courses = WebsiteCourseFirstPage.search([
        ('active','=',True)
        ],
        order=[('date','DESC'),
        ('id','DESC')])
    students = Subscription.search([])
    number_of_students = int(len(students)) + 1618
    form = ContactForm()
    if form.validate_on_submit():

        firstname = form.firstname.data
        email = form.email.data
        phone = form.phone.data
        city = form.city.data
        method = dict(form.method.choices).get(form.method.data)
        today = date.today()

        url = "https://app.verify-email.org/api/v1/BHCgLkl5zWE5txaMR2HJBg1OoJourpTumiNflw40wYQc4na0rw/verify/"#support@verify-email.org"
        response = requests.get( url=url + email)
        response_content = response.json()

        if response_content['status'] == 1:
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
            if phone is not None:
                ContactMechanism.create([{
                    'party': party1.id,
                    'type': 'phone',
                    'value': phone,
                    }])[0]
            if city is not None:
                address1, = Address.create([{
                    'party': party1.id,
                    'city': city,
                    }])

            session['firstname'] = firstname

            curso = dict(form.course.choices).get(form.course.data)

            body = "Hemos recibido la siguiente informacion (IND): " + " \n " + \
                "Nombre: "+ firstname + "\n Email: "+ email + " \n Telefono: " + phone + \
                " \n  Ciudad: " + city + " \n  Curso: " + curso + \
                "\n Forma de contacto: " + method

            msg = Message('Contacto APIXela: '+\
                firstname, sender = 'info@apixela.net', \
                recipients = [email, 'info@apixela.net'])
            msg.body = "Contacto Fb Ads :: " + body
            mail.send(msg)

            params = {}
            params['api_key'] = current_app.config['NEWSLETTER_API']
            params['list'] = current_app.config['NEWSLETTER_LIST']
            params['boolean'] = 'true'
            params['name'] = firstname
            params['email'] = email
            headers  = {'Content-type':'application/x-www-form-urlencoded',
            'charset':'UTF-8'}
            try:
                subscribe_url = current_app.config['NEWSLETTER_URL']
                subscribe_response = requests.post( url=subscribe_url,
                    data=params, headers=headers)
            except Exception:
                pass

            return redirect(url_for('main.welcome'))
        else:
            flash('Tu correo no es válido o está inactivo, intenta de nuevo')
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('index.html',user=user,
            form=form, firstpage=firstpage, courses=courses,
            number_of_students=number_of_students)
    return render_template('index.html', form=form,
        firstpage=firstpage, courses=courses,
        number_of_students=number_of_students)

@bp.errorhandler(404)
@bp.route('/contacto', methods=['GET', 'POST'])
@tryton.transaction(readonly=False, user=1)
def contact():

    form = ContactForm()
    if form.validate_on_submit():

        firstname = form.firstname.data
        email = form.email.data
        phone = form.phone.data
        city = form.city.data
        today = date.today()
        method = dict(form.method.choices).get(form.method.data)

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

        session['firstname'] = firstname

        curso = dict(form.course.choices).get(form.course.data)
        body = "Hemos recibido la siguiente informacion: " + " \n " + \
            "Nombre: "+ firstname + "\n Email: "+ email + " \n Telefono: " + phone + \
            " \n  Ciudad: " + city + " \n  Curso: " + curso + \
            "\n Forma de contacto: " + method

        msg = Message('Contacto APIXela: '+firstname, sender = 'info@apixela.net', recipients = [email, 'info@apixela.net'])
        msg.body = "Contacto Fb Ads " + body
        mail.send(msg)

        params = {}
        params['api_key'] = current_app.config['NEWSLETTER_API']
        params['list'] = current_app.config['NEWSLETTER_LIST']
        params['boolean'] = 'true'
        params['name'] = firstname
        params['email'] = email
        headers  = {'Content-type':'application/x-www-form-urlencoded',
        'charset':'UTF-8'}

        try:
            subscribe_url = current_app.config['NEWSLETTER_URL']
            subscribe_response = requests.post( url=subscribe_url,
                data=params, headers=headers)
        except Exception:
            pass

        return redirect(url_for('main.welcome'))
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('contacto.html', user=user,
            form=form)
    return render_template('contacto.html', form=form,)

@bp.errorhandler(404)
@bp.route('/presenciales/<slug>/')
@tryton.transaction(readonly=False,user=1)
def detail(slug):
    courses = WebsiteCourseFirstPage.search([('slug','=',slug)])
    if len(courses)==1:
        if current_user.is_authenticated:
            user = User(current_user)
            return render_template('main-course.html', courses=courses, user=user)
        return render_template('main-course.html', courses=courses)

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

'''
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
'''
'''
@bp.route('/computacion')
@tryton.transaction(readonly=False, user=1)
def computacion():
    if current_user.is_authenticated:
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        return render_template('computacion.html',user=user)
    return render_template('computacion.html')
'''

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
@bp.route('/compra', methods=['GET', 'POST'])
@tryton.transaction(readonly=False, user=1)
def buy():
    return redirect(url_for('course.enroll'))

@bp.route('/registro', methods=['GET'])
@tryton.transaction(readonly=False, user=1)
def register():
    return redirect(url_for('course.enroll'))

@bp.route('/servicios/<code>')
@login_required
@tryton.transaction(readonly=False, user=1)
def subscription_render(code):
    subscriptions = Subscription.search([('subscription_code','=',code)])
    if len(subscriptions)>=1:
        if current_user.is_authenticated:
            user = User(current_user)
            return render_template('digital_certificate.html',
                subscriptions=subscriptions,
                user=user,
                )
        return render_template('digital_certificate.html',
            subscriptions=subscriptions,)
    else:
        return redirect(url_for('main.welcome'))

@bp.route('/faq')
@tryton.transaction(readonly=False, user=1)
def faq():
    return redirect(url_for('course.faq'))