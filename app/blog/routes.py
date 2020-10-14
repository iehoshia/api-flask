from flask import render_template, redirect, url_for, \
    flash, request, current_app
from flask_login import current_user, login_required
from flask_paginate import Pagination, get_page_args

from werkzeug.urls import url_parse
from flask_babel import _
from app.blog import bp
from app.models import Entry, User
from app import tryton

@bp.route('/', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def index():
    posts_per_page = current_app.config['POSTS_PER_PAGE']
    page, per_page, offset = get_page_args()
    domain = [('published','=',True),
        ('category.slug','=','api')]
    entries = Entry.search(domain,
        order=[('date', 'DESC'), ('id','DESC')],
        offset=offset, limit=per_page
        )
    count = Entry.search(domain, count=True)
    pagination = Pagination(
        page=page, total=count, search=False)
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('blog/post.html',
            entries=entries, title=_('Blog'),
            user=user, pagination=pagination)
    return render_template('blog/post.html',
        entries=entries, title=_('Blog'),
        pagination=pagination)


@bp.errorhandler(404)
@bp.route('/<slug>/')
@tryton.transaction(readonly=False,user=1)
def detail(slug):
    if slug:
        entries = Entry.search([('slug','=',slug)])
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

@bp.route('/iehoshia', methods=['GET', 'POST'])
@tryton.transaction(readonly=False,user=1)
def personal():
    posts_per_page = current_app.config['POSTS_PER_PAGE']
    page, per_page, offset = get_page_args()
    domain = [('published','=',True),
        ('category.slug','=','personal')]
    entries = Entry.search(domain,
        order=[('date', 'DESC'), ('id','DESC')],
        offset=offset, limit=per_page
        )
    count = Entry.search(domain, count=True)
    pagination = Pagination(
        page=page, total=count, search=False)
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('blog/personal-post.html',
            entries=entries, title=_('Blog'), user=user,
            pagination=pagination)
    return render_template('blog/personal-post.html',
        entries=entries, title=_('Blog'),
        pagination=pagination)

@bp.errorhandler(404)
@bp.route('/iehoshia/<slug>/')
@tryton.transaction(readonly=False,user=1)
def personal_detail(slug):
    if slug:
        entries = Entry.search([('slug','=',slug)])
        #print ("ENTRY::",str(entries))
        if len(entries)>=1:
            user = None
            if current_user.is_authenticated:
                user = User(current_user)
                return render_template('blog/personal-detail.html', entries=entries, user=user)
            return render_template('blog/personal-detail.html',entries=entries)
    if current_user.is_authenticated:
        user = User(current_user)
        return render_template('404.html', user=user),404
    return render_template('404.html'), 404