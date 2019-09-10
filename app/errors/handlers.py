from flask import render_template, request
from app import db, tryton
from app.errors import bp
from app.api.errors import error_response as api_error_response
from flask_login import current_user, login_required

User = tryton.pool.get('web.user')

def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']


@bp.app_errorhandler(404)
@tryton.transaction(readonly=False,user=1)
def not_found_error(error):
    if wants_json_response():
        return api_error_response(404)
    if current_user.is_authenticated:
        #current_id = current_user.get_id()
        #user, = User.search([('id','=',current_id)])
        username_id = current_user.get_id()
        user, = User.search([('id','=',username_id)])
        print("USER",str(user))
        return render_template('errors/404.html',user=user), 404
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500)
    return render_template('errors/500.html'), 500
