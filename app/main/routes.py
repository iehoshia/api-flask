from datetime import datetime, date
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, session, request

from flask_login import current_user, login_required
from flask_babel import _, get_locale
#from guess_language import guess_language
from app import db, tryton, mail
from app.main.forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app.models import User, Post, Notification #, Message
from app.translate import translate
from app.main import bp
from app.forms import ContactForm
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

'''
@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        #language = guess_language(form.post.data)
        language = 'es'
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.post.data, author=current_user,
                    language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)
'''

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('main.user', username=username))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)

'''
@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)
'''

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@tryton.transaction(readonly=False, user=1)
#@tryton.transaction()
def index():
    form = ContactForm() 
    #if request.method == 'POST':
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
    return render_template('index.html', form=form)
    #else:
    #    return render_template('index.html', form=form) 
 
@bp.route('/bienvenido')
def welcome():
    if 'firstname' in session: 
        firstname = session['firstname']
        return render_template('bienvenido.html', firstname=firstname) 
    else:
        return redirect('/')

@bp.route('/cine')
def cine():
    return render_template('cine.html')

@bp.route('/reparacion')
def reparacion():
    return render_template('reparacion.html')

@bp.route('/ingles')
def ingles():
    return render_template('ingles.html')

@bp.route('/powerpivot')
def powerpivot():
    return render_template('powerpivot.html')

@bp.route('/diseno')
def diseno():
    return render_template('diseno.html')

@bp.route('/computacion')
def computacion():
    return render_template('computacion.html')

@bp.route('/produccion')
def produccion():
    return render_template('produccion.html')

@bp.route('/mikrotik')  
def mikrotik():
    return render_template('mikrotik.html')

@bp.route('/programacion')
def programacion():
    return render_template('programacion.html')

@bp.route('/construccion')
def construccion():
    return render_template('construccion.html') 

@bp.route('/privacidad')
def privacidad():
    return render_template('privacidad.html') 
