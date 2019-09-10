from time import time
import requests, random
from app import tryton
from app.course import bp
from app.course.forms import EnrollForm, EnrollRegistrationForm, \
    CreditCardForm, CancelEnrollForm, LessonCommentForm
from app.models import Course, User, Lesson, \
    Subscription, SubscriptionLine, Service, \
    Invoice, Journal, MoveLine, Product, SaleSubscriptionLine, \
    PaymentTerm, Payment, PaymentGroup, LessonComment
from card_identifier.card_type import identify_card_type
from card_identifier.cardutils import validate_card
from datetime import datetime, date
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from flask_babel import _
import json
from itertools import groupby
from werkzeug.urls import url_parse
from .codes import get_code

def uniqid(prefix = ''):
    return prefix + hex(int(time()))[2:10] + hex(int(time()*1000000) % 0x100000)[2:7]

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def index():
    courses = Course.search([('published','=',True)],
        order=[('id','DESC')])
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('course/course.html', courses=courses, title=_('Course'), user=user)
    return render_template('course/course.html', courses=courses, title=_('Course'))

@bp.errorhandler(404)
@bp.route('/<slug>/')
@login_required
@tryton.transaction(readonly=False,user=1)
def detail(slug):
    courses = Course.search([('slug','=',slug)])
    if len(courses)==1:
        if current_user.is_authenticated:
            user = User(current_user)
            return render_template('course/detail.html', courses=courses, user=user)
        return render_template('course/detail.html', courses=courses)
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('404.html',user=user), 404
    return render_template('404.html'), 404

@bp.errorhandler(404)
@bp.route('/<base>/<slug>/',methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def lesson(base, slug):
    if base and slug:
        lessons = Lesson.search([
            ('course.slug','=',base),
            ('slug','=',slug)
        ])
        if len(lessons)==1:
            user = User(current_user)
            form = LessonCommentForm()
            comments = LessonComment.search([('lesson','=',lessons[0].id)],
                order=[('id','DESC')])

            defaults = {}
            defaults['lessons'] = lessons
            defaults['course'] = base
            defaults['user'] = user
            defaults['form'] = form

            if len(comments)>0:
                defaults['comments'] = comments
            else:
                defaults['comments'] = []

            if form.validate_on_submit():
                content = form.comment_content.data
                comment, = LessonComment.create([{
                    'content':content,
                    'user':user.id,
                    'lesson':lessons[0].id,
                    }])
                #defaults['comments'].append(comment)
                #return render_template('course/lesson.html', **defaults)
                return redirect(url_for('course.lesson',base=base,slug=slug))
            if lessons[0].membership_type == 'free':
                return render_template('course/lesson.html', **defaults)
            elif lessons[0].membership_type == 'premium' and user.active_membership:
                return render_template('course/lesson.html', **defaults)
            else:
                return redirect(url_for('course.enroll'))
    user = User(current_user)
    return render_template('404.html',user=user), 404

@bp.route('/compra/',methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def enroll():
    user = User(current_user)
    if user.active_membership:
        return redirect(url_for('course.index'))
    party = user.party
    subscriptions = Subscription.search([
        ('party','=',party.id),
        ('state','=','running')
        ]
    )
    today = date.today()
    if len(subscriptions)>=1:
        return redirect(url_for('course.payment'))
    else:
        form = EnrollForm()
        if form.validate_on_submit():
            membership = form.membership.data
            services = Service.search([('product.code','=',membership)], limit=1)
            if len(services)==1:
                service, = services
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
        return render_template('course/enroll.html',user=user,form=form)

@bp.route('/compra-mensual/',methods=['POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def monthly_enroll():
    user = User(current_user)
    if user.active_membership:
        return redirect(url_for('course.index'))
    party = user.party
    subscriptions = Subscription.search([
        ('party','=',party.id),
        ('state','=','running')
        ]
    )
    today = date.today()
    if len(subscriptions)>=1:
        return redirect(url_for('course.payment'))
    else:
        membership = 'MONTHLY'
        services = Service.search([('product.code','=',membership)], limit=1)
        if len(services)==1:
            service, = services
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

@bp.route('/compra-anual/',methods=[ 'POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def yearly_enroll():
    user = User(current_user)
    if user.active_membership:
        return redirect(url_for('course.index'))
    party = user.party
    subscriptions = Subscription.search([
        ('party','=',party.id),
        ('state','=','running')
        ]
    )
    today = date.today()
    if len(subscriptions)>=1:
        return redirect(url_for('course.payment'))
    else:
        membership = 'YEARLY'
        services = Service.search([('product.code','=',membership)], limit=1)
        if len(services)==1:
            service, = services
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
    user = User(current_user)
    party = user.party
    today = date.today()
    if user.active_membership:
        return redirect(url_for('main.welcome'))
    subscriptions = Subscription.search([
        ('party','=',party.id),
        ('state','=','running')
        ]
    )
    invoices = Invoice.search([('party','=',party.id),
            ('state','=','posted'),
        ], limit=1)

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
        url_test = 'https://sandbox.qpaypro.com/payment/api_v1'
        url_production = 'https://payments.qpaypro.com/checkout/api_v1'

        if cc_form.validate_on_submit():
            credit_card = str(cc_form.card_number.data)
            credit_card.replace(' ','')
            invoice, = invoices

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
                Invoice.card_payment_succeed(invoices,reference=transaction_id)
            return render_template('bienvenido.html', flash_message=message,user=user)
        return render_template('course/pay_enroll.html',
            **defaults)
    elif len(subscriptions)>=1 and user.party.receivable!=0:
        return render_template('bienvenido.html',user=user,flash_message="Something wrong. Sorry the inconvenient. We will call you later.")
    else:
        return redirect(url_for('course.enroll'))

@bp.route('/cancelar/',methods=['GET','POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def cancel_subscription():
    user = User(current_user)
    party = user.party

    subscriptions = Subscription.search([
        ('party','=',party.id),
        ('state','=','running')
        ]
    )

    invoices = Invoice.search([('party','=',party.id),
            ('state','=','posted')
        ])
    cancel_form = CancelEnrollForm()

    def _group_payment_key(payment):
        return (('journal', payment.journal.id), ('kind', payment.kind))

    def _new_group(values):
        return PaymentGroup(**values)

    if len(subscriptions)>0 or len(invoices)>0:
        if cancel_form.validate_on_submit():
            if len(subscriptions)>0:
                for subscription in subscriptions:
                    Subscription.draft([subscription])
                    Subscription.cancel([subscription])
            if len(invoices)>0:
                Invoice.cancel_payment(invoices)
            return redirect(url_for('course.index'))
    return render_template('course/cancel_enroll.html',
        user=user,
        cancel_form=cancel_form,
        invoices=invoices,
        subscriptions=subscriptions)

@bp.route('/pago-banco/',methods=['GET','POST'])
@tryton.transaction(readonly=False,user=1)
@login_required
def pay_with_bank():
    user = User(current_user)
    party = user.party
    today = date.today()
    if user.active_membership:
        return redirect(url_for('main.welcome'))
    subscriptions = Subscription.search([
        ('party','=',party.id),
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
            return redirect(url_for('main.welcome'))
        return render_template('course/pay_enroll_with_bank.html',
            user=user,
            enroll_form=enroll_form,
            invoices=invoices,
            subscriptions=subscriptions)
    else:
        return redirect(url_for('course.enroll'))

