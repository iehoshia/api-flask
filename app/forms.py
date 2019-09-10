from flask_wtf import FlaskForm, RecaptchaField
from wtforms import RadioField, StringField, SelectField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo

class ContactForm(FlaskForm):
    firstname = StringField('',
    	validators=[DataRequired()],
    	render_kw={"placeholder": "Nombre *",
    	})
    email = StringField('',
    	validators=[DataRequired(), Email()],
    	render_kw={"placeholder": "Correo electronico *"})
    phone = StringField('',
    	validators=[DataRequired()],
    	render_kw={"placeholder": "Telefono *"})
    city = StringField('',
    	validators=[DataRequired()],
    	render_kw={"placeholder": "Ciudad *"})
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
        		  ],
    	validators=[DataRequired()],
    	render_kw={"placeholder": "Curso *"} )

    submit = SubmitField('Comienza AHORA')