from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import ValidationError, DataRequired, Length, Email, EqualTo
from flask_babel import _, lazy_gettext as _l
from app.models import User
from app import tryton

Service = tryton.pool.get('sale.subscription.service')


@tryton.transaction(readonly=False, user=1)
def default_services():
    choices = []
    services = Service.search([])
    if len(services)>0:
        for service in services:
            choices.append(service.id, service.name)
    return choices

#@tryton.transaction(readonly=False, user=1)
class ContactForm(FlaskForm):

    firstname = StringField('',
        validators=[DataRequired()],
        render_kw={"placeholder": "Nombre *",
        })
    email = StringField('',
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Correo electronico *"})
    phone = StringField('',
        validators=[],
        render_kw={"placeholder": "Teléfono (opcional)"})
    city = StringField('',
        validators=[],
        render_kw={"placeholder": "Ciudad (opcional)"})
    method = SelectField(
        ('Método de contacto'),
        choices=[
                  ('1', _l('Teléfono')),
                  ('2', _l('Correo')),
                  ],
        validators=[DataRequired()],
        default=2,
        render_kw={"placeholder": "Forma de contacto preferido"} )
    course = SelectField(
        ('Curso'),
        choices=[
                  ('1', _l('Reparación de Software de Celulares')),
                  ('8', _l('Reparación de Computadoras')),
                  ('2', _l('Diseño Publicitario')),
                  ('3', _l('Idioma Ingles')),
                  ('4', _l('Redes informáticas')),
                  ('5', _l('Computacion, Ofimática y Cloud Computing')),
                  ('6', _l('Programación Basica y Web')),
                  ('7', _l('Inteligencia de Negocios en Excel')),
                  ],
        validators=[DataRequired()],
        render_kw={"placeholder": "Curso *"} )

    #course = SelectMultipleField( choices = default_services )
    submit = SubmitField('ENVIAR',
        render_kw={"class":"call-to-us"},
        )


class EditProfileForm(FlaskForm):
    email = StringField(_l('Email'),
        validators=[DataRequired()],
        render_kw={'readonly':True},
        )
    name = StringField(_l('Name'),
        validators=[DataRequired()],
        )
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=280)])
    submit = SubmitField(_l('Submit'))

    #def __init__(self, original_username, *args, **kwargs):
    #    super(EditProfileForm, self).__init__(*args, **kwargs)
    #    self.original_username = original_username

    #def validate_username(self, username):
    #    if username.data != self.original_username:
    #        user = User.query.filter_by(username=self.username.data).first()
    #        if user is not None:
    #            raise ValidationError(_('Please use a different username.'))


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))


class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)


class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))
