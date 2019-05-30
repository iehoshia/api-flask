import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_babel import _, lazy_gettext as _l
from app.models import User

class LoginForm(FlaskForm):
    username = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

class RegistrationForm(FlaskForm):
    username = StringField(_l('Name'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    phone = StringField(_l('Phone Number'), validators=[DataRequired()])
    city = StringField(_l('City'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    course = SelectField(
    #course = SelectMultipleField(    
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
    submit = SubmitField(_l('Register'))

    def validate_password(self, password):
        password = password.data
        if not re.match(r"^(?=.*[\d])(?=.*[A-Z])(?=.*[a-z])(?=.*[@#$])[\w\d@#$]{6,12}$", password):
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
    phone = StringField(_l('Phone Number'), validators=[DataRequired()])
    city = StringField(_l('City'), validators=[DataRequired()])
    course = SelectField(
    #course = SelectMultipleField(    
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
    submit = SubmitField(_l('Register'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))
