from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from werkzeug.urls import url_parse
from flask_babel import _
from app.blog import bp
from app.models import Entry, User
from app import tryton

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def index():
    entries = Entry.search([('published','=',True)],
        limit=6)
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('blog/post.html', entries=entries, title=_('Blog'), user=user)
    return render_template('blog/post.html', entries=entries, title=_('Blog'))

@bp.errorhandler(404)
@bp.route('/<slug>/')
@tryton.transaction(readonly=False,user=1)
def detail(slug):
    if slug:
        entries = Entry.search([('slug','=',slug)])
        #print ("ENTRY::",str(entries))
        if len(entries)>=1:
            user = None
            if current_user.is_authenticated:
                user = User(current_user)
                return render_template('blog/detail.html', entries=entries, user=user)
            return render_template('blog/detail.html',entries=entries)
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('404.html', user=user),404
    return render_template('404.html'), 404