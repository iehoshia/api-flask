import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, \
    SubmitField, SelectField, FloatField, DateField, \
    IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from wtforms.widgets import TextArea
from flask_babel import _, lazy_gettext as _l
from app.models import User

class EnrollForm(FlaskForm):
    membership = SelectField(
        (_l('Membership')),
        choices=[
                  ('MONTHLY', _l('Monthly')),
                  ('YEARLY', _l('Yearly')),
                  ],
        validators=[DataRequired()],
        )
    submit = SubmitField(_('Activate'))

class EnrollRegistrationForm(FlaskForm):
    invoice = StringField(_l('Invoice'), render_kw={'readonly':True,})# validators=[DataRequired()])
    amount = FloatField(_l('Amount'),render_kw={'readonly':True,})# validators=[DataRequired()])
    bank = StringField(_l('Bank'), validators=[],render_kw={'placeholder':_l('BANRURAL'),'readonly':True})
    account_name = StringField(_l('Account Name'), validators=[],render_kw={'placeholder':_l('API CENTRO DE CAPACITACION'),'readonly':True})
    account = StringField(_l('Account'), validators=[],render_kw={'placeholder':_l('3313010396'),'readonly':True})
    ticket = StringField('', validators=[DataRequired()],render_kw={'autofocus': True, 'placeholder':_l('Ticket'),})
    submit = SubmitField(_l('Submit'))

class CreditCardForm(FlaskForm):
    name = StringField(_l('Credit Card Name'), validators=[DataRequired()],
        render_kw={'placeholder': _('JUAN RAMOS'),
        'maxlength':40,
        'class':'form-control',})
    card_number = StringField(_l('Credit Card Number'), validators=[DataRequired()],
        render_kw={'placeholder': _('4000 0000 0000 0002'),'autocomplete':'off',
        'maxlength':19,
        'class':'form-control',})
    expiration_date = StringField(_l('Expiry Date'), validators=[DataRequired()],
        render_kw={'placeholder': _('mm/aa'),'autocomplete':'off',
        'maxlength':5,
        'class':'form-control',})
    code = IntegerField(_l('CVV'), validators=[DataRequired()],
        render_kw={'placeholder': _('123'),'autocomplete':'off',
        'maxlength':4,
        'class':'form-control',})
    submit = SubmitField(_l('Submit'))

class CancelEnrollForm(FlaskForm):
    accept = BooleanField(_l('Do you want to cancel'))
    submit = SubmitField(_l('Submit'))

class LessonCommentForm(FlaskForm):
    #username = StringField('Username')
    comment_content = StringField(_l('Comment content'), validators=[DataRequired()],
      render_kw={'placeholder': _('Write question here!'), 'autocomplete':'off',
      'autofocus': True,}, widget=TextArea(),
      )
    submit = SubmitField(_l('Submit'),)
