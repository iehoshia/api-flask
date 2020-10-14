import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_babel import _, lazy_gettext as _l
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('', validators=[DataRequired(), Email()], render_kw={"placeholder": "Email"})
    password = PasswordField('', validators=[DataRequired()], render_kw={"placeholder": _l("Password")})
    #remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Submit'))

class RegistrationForm(FlaskForm):
    username = StringField('', validators=[DataRequired()],render_kw={"placeholder": _l("Name")})
    email = StringField('', validators=[DataRequired(), Email()], render_kw={"placeholder": _l("Email")})
    phone = StringField('', validators=[DataRequired()], render_kw={"placeholder": _l("Phone Number")})
    city = StringField('', validators=[DataRequired()], render_kw={"placeholder": _l("City")})
    password = PasswordField('', validators=[DataRequired()], render_kw={"placeholder": _l("Password")})
    password2 = PasswordField(
        '', validators=[DataRequired(),
                                           EqualTo('password')], render_kw={"placeholder": _l("Repeat Password")})
    #course = SelectMultipleField(
    '''
    course = SelectField(
        ('Curso'),
        choices=[
                  ('1', 'Reparacion de Computadoras y Celulares'),
                  ('2', 'Diseno Publicitario'),
                  ('3', 'Ingles'),
                  ('4', 'Mikrotik y Ubiquiti'),
                  ('5', 'Computacion, Ofimatica y Cloud Computing'),
                  ('6', 'Programacion Basica y Web'),
                  ('7', 'Power Pivot: Inteligencia de Negocios'),
                  #('10', 'Produccion Musical'),
                  ],
        validators=[DataRequired()],
        render_kw={"placeholder": "Curso *"} )
    '''
    submit = SubmitField(_l('Register'))

    def validate_password(self, password):
        password = password.data
        #if not re.match(r"^(?=.*[\d])(?=.*[A-Z])(?=.*[a-z])(?=.*[@#$])[\w\d@#$]{6,12}$", password):
        if not re.match(r"[A-Za-z0-9@#$%^&+=]{6,12}", password):
            raise ValidationError(_('Password must contain special characters, number and uppercase letters.'))

    def validate_email(self, email):
        user = User.search([('email','=',email.data)])
        if len(user)==1:
            raise ValidationError(_('Email already used. Please use a different email.'))

    #def validate_email(self, email):
    #    user = User.query.filter_by(email=email.data).first()
    #    if user is not None:
    #s        raise ValidationError(_('Please use a different email address.'))

class CompleteRegistrationForm(FlaskForm):
    #password = PasswordField(_l('Password'), validators=[DataRequired()])
    #password2 = PasswordField(
    #    _l('Repeat Password'), validators=[DataRequired(),
    #                                       EqualTo('password')])
    phone = StringField('', validators=[DataRequired()], render_kw={"placeholder": _l("Phone Number")})
    city = StringField('', validators=[DataRequired()], render_kw={"placeholder": _l("City")})
    #course = SelectMultipleField(
    '''
    course = SelectField(
        ('Curso'),
        choices=[
                  ('1', 'Reparacion de Computadoras y Celulares'),
                  ('2', 'Diseno Publicitario'),
                  ('3', 'Ingles'),
                  ('4', 'Mikrotik y Ubiquiti'),
                  ('5', 'Computacion, Ofimatica y Cloud Computing'),
                  ('6', 'Programacion Basica y Web'),
                  ('7', 'Power Pivot: Inteligencia de Negocios'),
                  #('10', 'Produccion Musical'),
                  ],
        validators=[DataRequired()],
        render_kw={"placeholder": "Curso *"} )
    '''
    submit = SubmitField(_l('Register'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('', validators=[DataRequired(), Email()],render_kw={"placeholder": _l("Email")})
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField('', validators=[DataRequired()],render_kw={"placeholder": _l("Password")})
    password2 = PasswordField(
        '', validators=[DataRequired(),
                                           EqualTo('password')], render_kw={"placeholder": _l("Repeat Password")})
    submit = SubmitField(_l('Request Password Reset'))
