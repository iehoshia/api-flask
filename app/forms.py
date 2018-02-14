# -*- coding: 850 -*-
# -*- coding: utf-8 -*- 
from flask_wtf import FlaskForm, RecaptchaField 
from wtforms import RadioField, StringField, SelectField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo 
class LoginForm(FlaskForm): 
    firstname = StringField('Nombre',   
    	validators=[DataRequired()],     
    	render_kw={"placeholder": "Nombre *", 
    	})    
    email = StringField('Correo electronico',       
    	validators=[DataRequired(), Email()], 
    	render_kw={"placeholder": "Correo electronico *"}) 
    phone = StringField('Telefono',   
    	validators=[DataRequired()],     
    	render_kw={"placeholder": "Telefono *"})  
    city = StringField('Ciudad',       
    	validators=[DataRequired()],            
    	render_kw={"placeholder": "Ciudad *"}) 
    course = SelectField(    
        'Curso de interes', 
        choices=[ ('1', 'Reparacion de Computadoras y Celulares'), 
        		  ('2', 'Diseno Publicitario'), 
        		  ('3', 'Comunicacion y Produccion Cinematografica'),
                  ('4', 'Ingles'),
                  ('5', 'Computacion, Ofimatica y Cloud Computing'),
                  ('6', 'Mikrotik y Ubiquiti'),
                  ('7', 'Construccion Digital en Arquitectura: AutoCAD'),
                  ('8', 'Produccion Musical'),
                  ('9', 'Programacion Basica y Web'),
        		  ],
    	validators=[DataRequired()],
    	render_kw={"placeholder": "Curso *"} )

    recaptcha = RecaptchaField()
    submit = SubmitField('Comienza AHORA')

   