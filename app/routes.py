from flask import render_template, flash, redirect, url_for, session
from flask_mail import Message 
from app import app
from app import tryton, mail 
from app.forms import LoginForm
import functions 
import datetime       
 
User = tryton.pool.get('res.user')
Party = tryton.pool.get('party.party')
ContactMechanism = tryton.pool.get('party.contact_mechanism')
Address = tryton.pool.get('party.address')
Opportunity = tryton.pool.get('sale.opportunity')
OpportunityLine = tryton.pool.get('sale.opportunity.line')

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

@tryton.default_context
def default_context():
	return User.get_preferences(context_only=True)

@app.route('/admin')
@tryton.transaction()
def hello():
	user, = User.search([('login', '=', 'admin')])
	return '%s, Hello World!' % user.name

'''@app.route('/add')
@tryton.transaction(readonly=False)
def add():
	party1, = Party.create([{
                    'name': 'Party 1', 
                    }])
	return "Done"
	#InternalError: cannot execute nextval() in a read-only transaction'''

@app.route('/', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def index():
	form = LoginForm() 
	if form.validate_on_submit():
		firstname = form.firstname.data
		email = form.email.data 
		phone = form.phone.data
		city = form.city.data
		today = datetime.date.today()
		service = form.course.data
		service = int(service)
		product = functions.get_product(service)
		party1, = Party.create([{
			'name': firstname,
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
			'description':'Contacto apixela.net: '+ firstname,
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

		'''send_email("Contacto APIXela" + firstname,
				'info@apixela.net',
				[email],
				curso,
				""
				)'''
		msg = Message('Contacto APIXela: '+firstname, sender = 'info@apixela.net', 
			recipients = [email,'info@apixela.net'])
		msg.body = "Contacto Fb Ads " + body
		mail.send(msg)

		return redirect('/bienvenido')
	return render_template('index.html', form=form) 
 
@app.route('/bienvenido')
def welcome():
	if 'firstname' in session: 
		firstname = session['firstname']
		return render_template('bienvenido.html', firstname=firstname) 
	else:
		return redirect('/')

@app.route('/cine')
def cine():
	return render_template('cine.html')

@app.route('/reparacion')
def reparacion():
	return render_template('reparacion.html')

@app.route('/ingles')
def ingles():
	return render_template('ingles.html')

@app.route('/diseno')
def diseno():
	return render_template('diseno.html')

@app.route('/computacion')
def computacion():
	return render_template('computacion.html')

@app.route('/produccion')
def produccion():
	return render_template('produccion.html')

@app.route('/mikrotik')  
def mikrotik():
	return render_template('mikrotik.html')

@app.route('/programacion')
def programacion():
	return render_template('programacion.html')

@app.route('/construccion')
def construccion():
	return render_template('construccion.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/tryton/user/<record("res.user"):user>')
@tryton.transaction()
def user(user):
	return user.name

@app.route('/tryton/users/<records("res.user"):users>')
@tryton.transaction()
def users(users):
	return ', '.join(u.name for u in users)