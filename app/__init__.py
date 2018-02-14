from raven.contrib.flask import Sentry
from flask import Flask
from flask_tryton import Tryton
from flask_bootstrap import Bootstrap
from flask_mail import Mail

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
Bootstrap(app)

tryton = Tryton(app)
sentry = Sentry(app)
mail = Mail(app)

from app import routes

if __name__ == "__main__":
    app.run()