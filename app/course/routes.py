import requests, random
import json
import ipinfo
import ipaddress
from time import time
from datetime import datetime, date
from app import tryton, mail
from flask_mail import Message
from app.course import bp
from app.course.forms import EnrollForm, EnrollRegistrationForm, \
    CreditCardForm, CancelEnrollForm, LessonCommentForm, \
    EnrollBankForm, EnrollCreditCardForm
from app.models import Course, User, Lesson, \
    Subscription, SubscriptionLine, Service, \
    Invoice, Journal, MoveLine, Product, SaleSubscriptionLine, \
    PaymentTerm, Payment, PaymentGroup, LessonComment, \
    Currency, Question
from card_identifier.card_type import identify_card_type
from card_identifier.cardutils import validate_card
from datetime import datetime, date
from flask import render_template, redirect, url_for, \
    flash, request, current_app
from flask_login import current_user, login_required
from flask_babel import _
from itertools import groupby
from werkzeug.urls import url_parse
from .codes import get_code
from .data import data
#from flask_tryton import tryton_transaction as Transaction
from trytond.transaction import Transaction

def uniqid(prefix = ''):
    return prefix + hex(int(time()))[2:10] + hex(int(time()*1000000) % 0x100000)[2:7]

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def index():
    courses = Course.search([('published','=',True)],
        order=[('position','DESC')])
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('course/course.html', courses=courses, title=_('Course'), user=user)
    return render_template('course/course.html', courses=courses, title=_('Course'))

@bp.errorhandler(404)
@bp.route('/<slug>/')
#@login_required
@tryton.transaction(readonly=False,user=1)
def detail(slug):
    courses = Course.search([('slug','=',slug)])
    if len(courses)==1:
        web_courses = Course.search([('slug','=',slug)],
        limit=1)
        web_course, = web_courses
        w_courses = []
        w_courses.append(web_course.service.id)
        w_courses.append(web_course.yearly_service.id)
        with Transaction().set_context(courses=w_courses):
            if current_user.is_authenticated:
                user = User(current_user)
                return render_template('course/detail.html',
                    courses=courses, user=user)
            return render_template('course/detail.html', courses=courses)
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('404.html',user=user), 404
    return render_template('404.html'), 404

@bp.errorhandler(404)
@bp.route('/<base>/<slug>/',methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
#@login_required
def lesson(base, slug):
    if base and slug:
        lessons = Lesson.search([
            ('course.slug','=',base),
            ('slug','=',slug)
        ])
        if len(lessons)==1:
            form = LessonCommentForm()
            comments = LessonComment.search([('lesson','=',lessons[0].id)],
                order=[('id','DESC')])

            defaults = {}
            defaults['lessons'] = lessons
            defaults['course'] = base
            defaults['form'] = form
            if current_user.is_authenticated:
                user = User(current_user)
                defaults['user'] = user

            if len(comments)>0:
                defaults['comments'] = comments
            else:
                defaults['comments'] = []

            if form.validate_on_submit() and current_user.is_authenticated:
                content = form.comment_content.data
                user = User(current_user)
                comment, = LessonComment.create([{
                    'content':content,
                    'user':user.id,
                    'lesson':lessons[0].id,
                    }])
                #defaults['comments'].append(comment)
                #return render_template('course/lesson.html', **defaults)
                return redirect(url_for('course.lesson', base=base, slug=slug))
            courses = []
            courses.append(lessons[0].course.service.id)
            courses.append(lessons[0].course.yearly_service.id)
            with Transaction().set_context(courses=courses):
                if lessons[0].membership_type == 'free':
                    return render_template('course/lesson.html', **defaults)
                elif lessons[0].membership_type == 'premium' and \
                        current_user.is_authenticated:
                    user = User(current_user)
                    if user.active_membership:
                        return render_template('course/lesson.html', **defaults)
                    else:
                        return redirect(url_for('course.enroll',
                            course=lessons[0].course.id))
                elif lessons[0].membership_type == 'premium' and \
                        not current_user.is_authenticated:
                    return redirect(url_for('auth.login',
                        next=request.url))
                else:
                    return redirect(url_for('course.enroll',
                        course=lessons[0].course.id))
    #if type(current_user) == 'AnonymousUserMixin':
    if not isinstance(current_user, int):
        return redirect(url_for('auth.login',
                        next=request.url))
    user = User(current_user)
    return render_template('404.html',user=user), 404

@bp.route('/enroll/',methods=['GET', 'POST'])
@bp.route('/compra/',methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def enroll():
    bank_form = EnrollBankForm()
    cc_form = EnrollCreditCardForm()

    course_id = request.args.get('course')
    base_url = request.url_root
    if course_id==None:
        return redirect(url_for('course.index'))
    course_id = int(course_id)
    user = User(current_user)
    web_courses = Course.search([('id','=',course_id)],
        limit=1)
    if len(web_courses)==1:
        web_course, = web_courses
    else:
        print("NOT COURSE FOUND")
        return redirect(url_for('course.index'))

    ip_address = request.remote_addr
    if not ip_address or ip_address=='127.0.0.1':
        ip_address = '186.189.195.217'
    if ipaddress.ip_address(ip_address).is_private:
        ip_address = '186.189.195.217'
    access_token = 'cda5ddffc1e6b7'
    handler = ipinfo.getHandler(access_token)

    details = handler.getDetails(ip_address)
    country_code = details.country
    country_code = str(country_code)
    lcase_country_code = country_code.lower()
    currency_id = 16

    for currency in data:
        if str(currency['code']) == country_code:
            currency_id = currency['id']
            break
    currency = Currency(currency_id)

    courses = []
    courses.append(web_course.service.id)
    courses.append(web_course.yearly_service.id)
    with Transaction().set_context(courses=courses):
        user = User(current_user)
        if user.active_membership:
            return redirect(base_url + '/cursos/' +
                web_course.slug)
            #return redirect(url_for('course.index', web_course.slug))
    party = user.party
    courses = Course.search([('id','=',course_id)], limit=1)
    today = date.today()
    if len(courses)==1:
        course, = courses
        service_id = course.service.id
        yearly_service_id = course.yearly_service.id
        product_id = course.service.product.id
        yearly_product_id = course.yearly_service.product.id
        # for local currency
        with Transaction().set_context(product_web=product_id,
            currency_web=currency_id):
            price_monthly = Product.get_webshop_sale_price([])
        with Transaction().set_context(product_web=yearly_product_id,
            currency_web=currency_id):
            price_yearly = Product.get_webshop_sale_price([])
        # for US currency
        with Transaction().set_context(product_web=product_id,
            currency_web=64):
            dollar_price_monthly = Product.get_webshop_sale_price([])
        with Transaction().set_context(product_web=yearly_product_id,
            currency_web=64):
            dollar_price_yearly = Product.get_webshop_sale_price([])
    subscriptions = Subscription.search([
        ('party','=',party.id),
        ('state','=','running'),
        ('is_online','=',True),
        ('lines.service','=',service_id),
        ])
    subscriptions_yearly = Subscription.search([
        ('party','=',party.id),
        ('state','=','running'),
        ('is_online','=',True),
        ('lines.service','=',yearly_service_id),
        ])

    if len(subscriptions)>=1 or len(subscriptions_yearly)>=1:
        return redirect(url_for('course.payment'))
    else:
        defaults = {}
        defaults['user'] = user
        defaults['course'] = course_id
        defaults['web_course'] = web_course
        defaults['price_monthly'] = price_monthly
        defaults['price_yearly'] = price_yearly
        defaults['dollar_price_monthly'] = dollar_price_monthly
        defaults['dollar_price_yearly'] = dollar_price_yearly
        defaults['currency'] = currency
        defaults['country_code'] = country_code
        defaults['country_code_iso'] = lcase_country_code
        defaults['bank_form'] = bank_form
        defaults['cc_form'] = cc_form
        return render_template('course/enroll.html', **defaults)

@bp.route('/compra-mensual/',methods=['GET','POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def monthly_enroll():
    course_id = request.args.get('course')
    if course_id==None:
        return redirect(url_for('course.index'))
    course_id = int(course_id)
    user = User(current_user)
    courses = []
    courses.append(course_id)
    with Transaction().set_context(courses=courses):
        user = User(current_user)
        if user.active_membership:
            return redirect(url_for('course.index'))
    courses = Course.search([('id','=',course_id)], limit=1)
    if len(courses)==1:
        course, = courses
        service_id = course.service.id
        service = Service(service_id)
    party = user.party
    today = date.today()
    subscriptions = Subscription.search([
        ('party','=',party.id),
        ('state','=','running'),
        ('is_online','=',True),
        ('lines.service','=',service_id),
        ])
    if len(subscriptions)>=1:
        return redirect(url_for('course.payment'))
    else:
        enrolment, = Product.search([('is_enrolment','=',True)], limit=1)
        payment_term, = PaymentTerm.search([()],limit=1)
        address = user.party.addresses[0]
        new_subscription = Subscription.create([{
            'party':user.party.id,
            'start_date':today,
            'invoice_start_date':today,
            'invoice_recurrence':service.consumption_recurrence,
            'enrolment':enrolment.id,
            'unit_price_enrolment':0,
            'invoice_address':address,
            'payment_term':payment_term.id,
            'is_online':True,
            }])
        new_subscription_line, = SubscriptionLine.create([{
            'subscription':new_subscription[0].id,
            'service':service.id,
            'quantity':1,
            'start_date':today,
            'consumption_recurrence':service.consumption_recurrence,
            'unit':1,
            'unit_price':service.product.list_price,
            }])
        Subscription.quote(new_subscription)
        Subscription.run(new_subscription)
        SaleSubscriptionLine.generate_consumption(date=today,party=user.party)
        Subscription.generate_invoice(date=today,party=user.party)
        invoices = Invoice.search([('party','=',user.party)])
        if len(invoices)>=1:
            for invoice in invoices:
                if invoice.state == 'draft':
                    Invoice.post([invoice])
        return redirect(url_for('course.payment'))

@bp.route('/compra-anual/',methods=['GET','POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def yearly_enroll():
    course_id = request.args.get('course')
    if course_id==None:
        return redirect(url_for('course.index'))
    course_id = int(course_id)
    user = User(current_user)
    courses = []
    courses.append(course_id)
    with Transaction().set_context(courses=courses):
        user = User(current_user)
        if user.active_membership:
            return redirect(url_for('course.index'))
    courses = Course.search([('id','=',course_id)], limit=1)
    if len(courses)==1:
        course, = courses
        service_id = course.yearly_service.id
        service = Service(service_id)
    party = user.party
    today = date.today()
    subscriptions = Subscription.search([
        ('party','=',party.id),
        ('state','=','running'),
        ('lines.service','=',service_id),
        ])
    if len(subscriptions)>=1:
        return redirect(url_for('course.payment'))
    else:
        enrolment, = Product.search([('is_enrolment','=',True)], limit=1)
        payment_term, = PaymentTerm.search([()],limit=1)
        address = user.party.addresses[0]
        new_subscription = Subscription.create([{
            'party':user.party.id,
            'start_date':today,
            'invoice_start_date':today,
            'invoice_recurrence':service.consumption_recurrence,
            'enrolment':enrolment.id,
            'unit_price_enrolment':0,
            'invoice_address':address,
            'is_online':True,
            'payment_term':payment_term.id,
            }])
        new_subscription_line, = SubscriptionLine.create([{
            'subscription':new_subscription[0].id,
            'service':service.id,
            'quantity':1,
            'start_date':today,
            'consumption_recurrence':service.consumption_recurrence,
            'unit':1,
            'unit_price':service.product.list_price,
            }])
        Subscription.quote(new_subscription)
        Subscription.run(new_subscription)
        SaleSubscriptionLine.generate_consumption(date=today,party=user.party)
        Subscription.generate_invoice(date=today,party=user.party)
        invoices = Invoice.search([('party','=',user.party)])
        if len(invoices)>=1:
            for invoice in invoices:
                if invoice.state == 'draft':
                    Invoice.post([invoice])
        return redirect(url_for('course.payment'))

@bp.route('/pago/',methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def payment():
    #FIX WHEN CREDIT CARD IS ACTIVE
    return redirect(url_for('course.pay_with_bank'))
    user = User(current_user)
    party = user.party
    today = date.today()
    courses = []
    subscriptions = Subscription.search([('is_online','=',True),
        ('party','=',party.id),
        ('state','=','running')])
    if len(subscriptions)<1:
        return render_template('bienvenido.html',
                    user=user,
                    flash_message="Something wrong. Sorry the inconvenient. We will call you later.")
    else:
        for subscription in subscriptions:
            for line in subscription.lines:
                courses.append(line.service.id)
    with Transaction().set_context(courses=courses):
        user = User(current_user)
        if user.active_membership:
            return redirect(url_for('course.index'))

    ip_address = request.remote_addr
    if not ip_address or ip_address=='127.0.0.1':
        ip_address = '186.189.195.217'
    if ipaddress.ip_address(ip_address).is_private:
        ip_address = '186.189.195.217'
    access_token = 'cda5ddffc1e6b7'
    handler = ipinfo.getHandler(access_token)

    details = handler.getDetails(ip_address)
    country_code = details.country
    country_code = str(country_code)
    lcase_country_code = country_code.lower()
    currency_id = 16

    for currency in data:
        if str(currency['code']) == country_code:
            currency_id = currency['id']
            break
    currency = Currency(currency_id)

    with Transaction().set_context(currency_web=currency_id):
        invoices = Invoice.search([('party','=',party.id),
                ('state','=','posted'),
            ])

    if len(subscriptions)>=1 and len(invoices)>=1:
        credentials = current_app.config['QPAYPRO_CREDENTIALS']
        cc_form = CreditCardForm()

        defaults = {}
        defaults['sessionid'] = uniqid()
        defaults['orgid'] = 'k8vif92e' #'1snn5n9w' TEST OR PRODUCTION
        defaults['merchantid'] = credentials['merchantid'] #'visanetgt_qpay'
        defaults['user'] = user
        defaults['cc_form'] = cc_form
        defaults['invoices'] = invoices
        defaults['subscriptions'] = subscriptions
        defaults['currency'] = currency

        url_test = 'https://sandbox.qpaypro.com/payment/api_v1'
        url_production = 'https://payments.qpaypro.com/checkout/api_v1'

        if cc_form.validate_on_submit():
            credit_card = str(cc_form.card_number.data)
            credit_card.replace(' ','')
            #invoice, = invoices
            success = True
            for invoice in invoices:
                params = {}
                params['x_login'] = credentials['x_login'] #'visanetgt_qpay'
                params['x_private_key'] = credentials['x_private_key'] # '88888888888'
                params['x_api_secret'] = credentials['x_api_secret'] #'99999999999'
                params['x_product_id'] = invoice.lines[0].product.id #6
                params['x_audit_number'] = random.randint(1,999999)
                params['x_fp_sequence'] = invoice.number #1988679099 #INVOICE SEQUENCE NUMBER
                params['x_invoice_num'] = invoice.id #random.randint(1,999999) #INVOICE SEQUENCE NUMBER
                params['x_fp_timestamp'] = time()
                params['x_currency_code'] = 'GTQ'
                params['x_amount'] = invoice.total_amount #1.00 #invoice.total_amount
                params['x_line_item'] = invoice.lines[0].product.name #'T-shirt Live Dreams<|>w01<|><|>1<|>1000.00<|>N'
                params['x_freight'] = 0.00
                params['x_email'] = 'jperez@apixela.net'
                params['cc_name'] = cc_form.name.data #'john doe'
                params['cc_number'] = credit_card #'4111111111111111'
                params['cc_exp'] =  str(cc_form.expiration_date.data) #'01/21'
                params['cc_cvv2'] =  cc_form.code.data #'4567'
                params['cc_type'] = 'visa'
                params['x_first_name'] =  user.party.name#'john'
                params['x_last_name'] =  user.party.name#'doe'
                params['x_company'] = 'API CENTRO' #'Company'
                params['x_address'] = user.party.city #'711-2880 Nulla'
                params['x_city'] = user.party.city #'Guatemala'
                params['x_state'] = user.party.city #'Guatemala'
                params['x_country'] = user.party.country #'Guatemala'
                params['x_zip'] = '09001'
                params['x_relay_response'] = 'none'
                params['x_relay_url'] = 'none'
                params['x_type'] = 'AUTH_ONLY'
                params['x_method'] = 'CC'
                params['http_origin'] = 'https://www.apixela.net' #'http://local.test.com'
                params['visaencuotas'] = 0
                params['device_fingerprint_id'] = defaults['sessionid']

                response = requests.post( url=url_production,
                    params=params)

                res = response.raise_for_status()
                response_content = response.json()

                #response_content = {'responseCode':"100",
                #    'idTransaction':"102030"}

                response_code = response_content['responseCode']
                message = get_code(response_code)

                if response_code == "00":
                    transaction_id = response_content['idTransaction']
                    Invoice.card_payment_succeed([invoice],
                        reference=transaction_id)
                else:
                    success = False
                    break
            if success:
                return render_template('bienvenido.html',
                    flash_message=message, user=user)
            else:
                return render_template('bienvenido.html',
                    user=user,
                    flash_message="Something wrong. Sorry the inconvenient. We will call you later.")
        return render_template('course/pay_enroll.html',
            **defaults)
    elif len(subscriptions)>=1 and user.party.receivable!=0:
        return render_template('bienvenido.html',
            user=user,
            flash_message="Something wrong. Sorry the inconvenient. We will call you later.")
    else:
        return redirect(url_for('course.index'))

@bp.route('/pago-banco/',methods=['GET','POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def pay_with_bank():
    user = User(current_user)
    party = user.party
    today = date.today()
    courses = []
    subscriptions = Subscription.search([('is_online','=',True),
        ('party','=',party.id),
        ('state','=','running')])
    if len(subscriptions)<1:
        return render_template('bienvenido.html',
                    user=user,
                    flash_message="Something wrong. Sorry the inconvenient. We will call you later.")
    else:
        for subscription in subscriptions:
            for line in subscription.lines:
                courses.append(line.service.id)
    with Transaction().set_context(courses=courses):
        if user.active_membership:
            return redirect(url_for('course.index'))


    ip_address = request.remote_addr
    if not ip_address or ip_address=='127.0.0.1':
        ip_address = '186.189.195.217'
    if ipaddress.ip_address(ip_address).is_private:
        ip_address = '186.189.195.217'
    access_token = 'cda5ddffc1e6b7'
    handler = ipinfo.getHandler(access_token)

    details = handler.getDetails(ip_address)
    country_code = details.country
    country_code = str(country_code)
    lcase_country_code = country_code.lower()
    currency_id = 16

    for currency in data:
        if str(currency['code']) == country_code:
            currency_id = currency['id']
            break
    currency = Currency(currency_id)

    subscriptions = Subscription.search([
        ('party','=',party.id),
        ('is_online','=',True),
        ('state','=','running')
        ]
    )

    invoices = Invoice.search([('party','=',party.id),
                ('state','=','posted'),
            ], limit=1)

    current_line = None
    for invoice in invoices:
        move = invoice.move
        lines = move.lines
        for line in lines:
            if line.debit > 0:
                current_line = MoveLine(line.id)
                break
    if current_line is not None:
        enroll_form = EnrollRegistrationForm(invoice=current_line.description,
            amount=current_line.debit)
    if len(subscriptions)>=1 and len(invoices)>=1:
        if enroll_form.validate_on_submit():
            def _group_payment_key(payment):
                return (('journal', payment.journal.id), ('kind', payment.kind))

            def _new_group(values):
                return PaymentGroup(**values)

            invoice = enroll_form.invoice.data
            amount = enroll_form.amount.data
            ticket = enroll_form.ticket.data
            if not current_line:
                return redirect(url_for('main.welcome'))
            journal, = Journal.search([('name','=','DCOMPENSA')],limit=1)
            new_payment = Payment.create([{
                    'journal':journal.id,
                    'kind':'receivable',
                    'party':party.id,
                    'line':current_line.id,
                    'description':ticket,
                    'amount':current_line.debit,
                }])
            Payment.approve(new_payment)
            payment, = new_payment
            groups = []
            new_payment = sorted(new_payment, key=_group_payment_key)
            for key, grouped_payments in groupby(new_payment,
                    key=_group_payment_key):
                def group():
                    group = _new_group(dict(key))
                    group.save()
                    groups.append(group)
                    return group
                Payment.process(list(grouped_payments), group)
            body = "Hemos recibido la siguiente informacion: " + \
                "Nombre: "+ party.name + \
                " \n  Ticket: " + ticket + \
                " \n  Usuario: " + user.email

            msg = Message('Usuario Web API: '+ party.name, \
                sender = 'info@apixela.net', \
                recipients = ['info@apixela.net'])
            msg.body = "Usuario Web API " + body
            mail.send(msg)

            return redirect(url_for('main.welcome'))
        return render_template('course/pay_enroll_with_bank.html',
            user=user,
            enroll_form=enroll_form,
            invoices=invoices,
            subscriptions=subscriptions,
            currency=currency)
    else:
        return redirect(url_for('course.index'))

@bp.route('/cancelar/',methods=['GET','POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def cancel_subscription():
    user = User(current_user)
    party = user.party

    subscriptions = Subscription.search([
        ('party','=',party.id),
        ('is_online','=',True),
        ('state','=','running')
        ]
    )

    invoices = Invoice.search([('party','=',party.id),
            ('state','=','posted')
        ])
    cancel_form = CancelEnrollForm()
    if len(subscriptions)==0 and len(invoices)==0:
        return redirect(url_for('course.index'))

    if len(subscriptions)>0 or len(invoices)>0:
        if cancel_form.validate_on_submit():
            if len(subscriptions)>0:
                for subscription in subscriptions:
                    Subscription.draft([subscription])
                    Subscription.cancel([subscription])
            if len(invoices)>0:
                for invoice in invoices:
                    Invoice.cancel([invoice])
            return redirect(url_for('course.index'))
    return render_template('course/cancel_enroll.html',
        user=user,
        cancel_form=cancel_form,
        invoices=invoices,
        subscriptions=subscriptions)

@bp.route('/matriculas/<code>')
@tryton.transaction(readonly=False, user=1)
def subscription_render(code):
    subscriptions = Subscription.search([('subscription_code','=',code)])
    if len(subscriptions)>=1:
        if current_user.is_authenticated:
            user = User(current_user)
            return render_template('course/digital_certificate.html',
                subscriptions=subscriptions,
                user=user,
                )
        return render_template('course/digital_certificate.html',
            subscriptions=subscriptions,)
    else:
        return redirect(url_for('main.welcome'))

@bp.route('/compra-tarjeta/',methods=['POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def buy_with_card():

    course_id = request.args.get('course')

    if course_id==None:
        return redirect(url_for('course.index'))

    bank_form = EnrollBankForm()
    cc_form = EnrollCreditCardForm()

    if cc_form.validate_on_submit():
        course_id = int(course_id)
        user = User(current_user)
        courses = []
        courses.append(course_id)
        with Transaction().set_context(courses=courses):
            user = User(current_user)
            if user.active_membership:
                return redirect(url_for('course.index'))
        courses = Course.search([('id','=',course_id)], limit=1)
        if len(courses)==1:
            course, = courses
            if cc_form.cc_membership.data == 'MONTHLY':
                service_id = course.service.id
            else:
                service_id = course.yearly_service.id
            service = Service(service_id)
        party = user.party
        today = date.today()
        subscriptions = Subscription.search([
            ('party','=',party.id),
            ('state','=','running'),
            ('is_online','=',True),
            ('lines.service','=',service_id),
            ])
        if len(subscriptions)>=1:
            return redirect(url_for('course.payment'))
        else:
            enrolment, = Product.search([('is_enrolment','=',True)], limit=1)
            payment_term, = PaymentTerm.search([()],limit=1)
            address = user.party.addresses[0]
            new_subscription = Subscription.create([{
                'party':user.party.id,
                'start_date':today,
                'invoice_start_date':today,
                'invoice_recurrence':service.consumption_recurrence,
                'enrolment':enrolment.id,
                'unit_price_enrolment':0,
                'invoice_address':address,
                'payment_term':payment_term.id,
                'is_online':True,
                }])
            new_subscription_line, = SubscriptionLine.create([{
                'subscription':new_subscription[0].id,
                'service':service.id,
                'quantity':1,
                'start_date':today,
                'consumption_recurrence':service.consumption_recurrence,
                'unit':1,
                'unit_price':service.product.list_price,
                }])
            Subscription.quote(new_subscription)
            Subscription.run(new_subscription)
            SaleSubscriptionLine.generate_consumption(date=today,party=user.party)
            Subscription.generate_invoice(date=today,party=user.party)
            invoices = Invoice.search([('party','=',user.party)],
                order=[('number', 'DESC')])
            if len(invoices)>=1:
                for invoice in invoices:
                    if invoice.state == 'draft':
                        Invoice.post([invoice])

            current_invoice = None
            for invoice in invoices:
                if invoice.state not in ['cancel', 'paid']:
                    current_invoice = invoice
                    break

            credentials = current_app.config['QPAYPRO_CREDENTIALS']
            cc_form = CreditCardForm()

            defaults = {}
            defaults['sessionid'] = uniqid()
            defaults['orgid'] = 'k8vif92e' #'1snn5n9w' TEST OR PRODUCTION
            defaults['merchantid'] = credentials['merchantid'] #'visanetgt_qpay'
            defaults['user'] = user
            defaults['cc_form'] = cc_form

            url_test = 'https://sandbox.qpaypro.com/payment/api_v1'
            url_production = 'https://payments.qpaypro.com/checkout/api_v1'

            credit_card = str(cc_form.card_number.data)
            credit_card.replace(' ','')

            success = True

            params = {}
            params['x_login'] = credentials['x_login'] #'visanetgt_qpay'
            params['x_private_key'] = credentials['x_private_key'] # '88888888888'
            params['x_api_secret'] = credentials['x_api_secret'] #'99999999999'
            params['x_product_id'] = current_invoice.lines[0].product.id #6
            params['x_audit_number'] = random.randint(1,999999)
            params['x_fp_sequence'] = current_invoice.number #1988679099 #INVOICE SEQUENCE NUMBER
            params['x_invoice_num'] = current_invoice.id #random.randint(1,999999) #INVOICE SEQUENCE NUMBER
            params['x_fp_timestamp'] = time()
            params['x_currency_code'] = 'GTQ'
            params['x_amount'] = current_invoice.total_amount #1.00 #invoice.total_amount
            params['x_line_item'] = current_invoice.lines[0].product.name #'T-shirt Live Dreams<|>w01<|><|>1<|>1000.00<|>N'
            params['x_freight'] = 0.00
            params['x_email'] = 'jperez@apixela.net'
            params['cc_name'] = cc_form.name.data #'john doe'
            params['cc_number'] = credit_card #'4111111111111111'
            params['cc_exp'] =  str(cc_form.expiration_date.data) #'01/21'
            params['cc_cvv2'] =  cc_form.code.data #'4567'
            params['cc_type'] = 'visa'
            params['x_first_name'] =  user.party.name#'john'
            params['x_last_name'] =  user.party.name#'doe'
            params['x_company'] = 'API CENTRO' #'Company'
            params['x_address'] = user.party.city #'711-2880 Nulla'
            params['x_city'] = user.party.city #'Guatemala'
            params['x_state'] = user.party.city #'Guatemala'
            params['x_country'] = user.party.country #'Guatemala'
            params['x_zip'] = '09001'
            params['x_relay_response'] = 'none'
            params['x_relay_url'] = 'none'
            params['x_type'] = 'AUTH_ONLY'
            params['x_method'] = 'CC'
            params['http_origin'] = 'https://www.apixela.net' #'http://local.test.com'
            params['visaencuotas'] = 0
            params['device_fingerprint_id'] = defaults['sessionid']
            params['bank_form'] = bank_form
            params['cc_form'] = cc_form

            response = requests.post( url=url_production,
                params=params)

            res = response.raise_for_status()
            response_content = response.json()

            #response_content = {'responseCode':"100",
            #    'idTransaction':"102030"}

            response_code = response_content['responseCode']
            message = get_code(response_code)

            if response_code == "00":
                transaction_id = response_content['idTransaction']
                Invoice.card_payment_succeed([current_invoice],
                    reference=transaction_id)
            else:
                success = False
                Subscription.draft(new_subscription)
                Subscription.cancel(new_subscription)
                Invoice.cancel([current_invoice])
            if success:
                return render_template('bienvenido.html',
                    flash_message=message, user=user)
            else:
                return render_template('bienvenido.html',
                    user=user,
                    flash_message=message,)
    return render_template('enroll.html', cc_form=cc_form,
        bank_form=bank_form)

@bp.route('/compra-banco/',methods=['GET','POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def buy_with_bank():
    course_id = request.args.get('course')
    if course_id==None:
        return redirect(url_for('course.index'))

    bank_form = EnrollBankForm()
    cc_form = EnrollCreditCardForm()
    course_id = int(course_id)
    user = User(current_user)
    courses = []
    courses.append(course_id)
    with Transaction().set_context(courses=courses):
        user = User(current_user)
        if user.active_membership:
            return redirect(url_for('course.index'))
    courses = Course.search([('id','=',course_id)], limit=1)
    if len(courses)==1:
        course, = courses
        if bank_form.bank_membership.data == 'MONTHLY':
            service_id = course.service.id
        else:
            service_id = course.yearly_service.id
        service = Service(service_id)
    if course:
        web_course = course

    ip_address = request.remote_addr
    if not ip_address or ip_address=='127.0.0.1':
        ip_address = '186.189.195.217'
    if ipaddress.ip_address(ip_address).is_private:
        ip_address = '186.189.195.217'
    access_token = 'cda5ddffc1e6b7'
    handler = ipinfo.getHandler(access_token)

    details = handler.getDetails(ip_address)
    country_code = details.country
    country_code = str(country_code)
    lcase_country_code = country_code.lower()
    currency_id = 16

    for currency in data:
        if str(currency['code']) == country_code:
            currency_id = currency['id']
            break
    currency = Currency(currency_id)

    if bank_form.validate_on_submit():
        party = user.party
        today = date.today()
        subscriptions = Subscription.search([
            ('party','=',party.id),
            ('state','=','running'),
            ('lines.service','=',service_id),
            ])
        if len(subscriptions)>=1:
            print("NO ACTIVE SUBSCRIPTIONS")
            return redirect(url_for('course.payment'))
        else:
            enrolment, = Product.search([('is_enrolment','=',True)], limit=1)
            payment_term, = PaymentTerm.search([()],limit=1)
            address = user.party.addresses[0]
            new_subscription = Subscription.create([{
                'party':user.party.id,
                'start_date':today,
                'invoice_start_date':today,
                'invoice_recurrence':service.consumption_recurrence,
                'enrolment':enrolment.id,
                'unit_price_enrolment':0,
                'invoice_address':address,
                'is_online':True,
                'payment_term':payment_term.id,
                }])
            new_subscription_line, = SubscriptionLine.create([{
                'subscription':new_subscription[0].id,
                'service':service.id,
                'quantity':1,
                'start_date':today,
                'consumption_recurrence':service.consumption_recurrence,
                'unit':1,
                'unit_price':service.product.list_price,
                }])
            Subscription.quote(new_subscription)
            Subscription.run(new_subscription)
            SaleSubscriptionLine.generate_consumption(date=today,
                party=user.party)
            Subscription.generate_invoice(date=today,party=user.party)
            invoices = Invoice.search([('party','=',user.party)],
                order=[('number', 'DESC')])
            if len(invoices)>=1:
                for invoice in invoices:
                    if invoice.state == 'draft':
                        Invoice.post([invoice])

            current_line = None
            current_invoice = None

            for invoice in invoices:
                if invoice.state not in ['cancel', 'paid']:
                    move = invoice.move
                    for line in move.lines:
                        if line.debit > 0:
                            current_line = MoveLine(line.id)
                            current_invoice = invoice
                            break
            if not current_line or not current_invoice:
                return redirect(url_for('main.welcome'))

            def _group_payment_key(payment):
                return (('journal', payment.journal.id),
                    ('kind', payment.kind))

            def _new_group(values):
                return PaymentGroup(**values)

            invoice = current_invoice
            amount = current_invoice.total_amount
            ticket = bank_form.ticket.data
            journal, = Journal.search([('name','=','DCOMPENSA')],limit=1)
            new_payment = Payment.create([{
                    'journal':journal.id,
                    'kind':'receivable',
                    'party':party.id,
                    'line':current_line.id,
                    'description':ticket,
                    'amount':current_line.debit,
                }])
            Payment.approve(new_payment)
            payment, = new_payment
            groups = []
            new_payment = sorted(new_payment, key=_group_payment_key)
            for key, grouped_payments in groupby(new_payment,
                    key=_group_payment_key):
                def group():
                    group = _new_group(dict(key))
                    group.save()
                    groups.append(group)
                    return group
                Payment.process(list(grouped_payments), group)
            body = "Hemos recibido la siguiente informacion: " + \
                "Nombre: "+ party.name + \
                " \n  Ticket: " + ticket + \
                " \n  Usuario: " + user.email

            msg = Message('Usuario Web API: '+ party.name, \
                sender = 'info@apixela.net', \
                recipients = ['info@apixela.net'])
            msg.body = "Usuario Web API " + body
            mail.send(msg)

            return redirect(url_for('main.welcome'))

    return render_template('course/enroll.html', cc_form=cc_form,
        bank_form=bank_form, user=user, web_course=course, 
        currency=currency)

@bp.errorhandler(404)
@bp.route('/faq/')
@tryton.transaction(readonly=False, user=1)
def faq():
    questions = Question.search([('active','=', True)])
    if len(questions)>0:
        if current_user.is_authenticated:
            user = User(current_user)
            return render_template('course/faq.html', questions=questions,
                user=user), 404
        return render_template('course/faq.html', questions=questions), 404
    return redirect(url_for('main.index'))