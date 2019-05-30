# This file is part of flask_tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from functools import wraps

from flask import request, current_app
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import BadRequest

try:
    from trytond import __version__ as trytond_version
except ImportError:
    from trytond.version import VERSION as trytond_version
trytond_version = tuple(map(int, trytond_version.split('.')))
try:
    from trytond.config import config
except ImportError:
    from trytond.config import CONFIG as config

from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.cache import Cache
from trytond import backend
from trytond.exceptions import UserError, UserWarning, ConcurrencyException

__version__ = '0.7'
__all__ = ['Tryton', 'tryton_transaction']


class Tryton(object):
    "Control the Tryton integration to one or more Flask applications."
    def __init__(self, app=None):
        self.context_callback = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        "Initialize an application for the use with this Tryton setup."
        database = app.config.setdefault('TRYTON_DATABASE', None)
        user = app.config.setdefault('TRYTON_USER', 0)
        configfile = app.config.setdefault('TRYTON_CONFIG', None)

        config.update_etc(configfile)

        # 3.0 compatibility
        if hasattr(config, 'set_timezone'):
            config.set_timezone()

        self.pool = Pool(database)
        with Transaction().start(database, user, readonly=True):
            self.pool.init()

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['Tryton'] = self
        app.url_map.converters['record'] = RecordConverter
        app.url_map.converters['records'] = RecordsConverter

    def default_context(self, callback):
        "Set the callback for the default transaction context"
        self.context_callback = callback
        return callback

    def _readonly(self):
        return not (request
            and request.method in ('PUT', 'POST', 'DELETE', 'PATCH'))

    @staticmethod
    def transaction(readonly=None, user=None, context=None):
        """Decorator to run inside a Tryton transaction.
        The decorated method could be run multiple times in case of
        database operational error.

        If readonly is None then the transaction will be readonly except for
        PUT, POST, DELETE and PATCH request methods.

        If user is None then TRYTON_USER will be used.

        readonly, user and context can also be callable.
        """
        DatabaseOperationalError = backend.get('DatabaseOperationalError')

        def get_value(value):
            return value() if callable(value) else value

        def instanciate(value):
            if isinstance(value, _BaseProxy):
                return value()
            return value

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                tryton = current_app.extensions['Tryton']
                database = current_app.config['TRYTON_DATABASE']
                if trytond_version >= (3, 3):
                    with Transaction().start(database, 0):
                        Cache.clean(database)
                else:
                    Cache.clean(database)

                if user is None:
                    transaction_user = get_value(
                        int(current_app.config['TRYTON_USER']))
                else:
                    transaction_user = get_value(user)

                if readonly is None:
                    is_readonly = get_value(tryton._readonly)
                else:
                    is_readonly = get_value(readonly)

                transaction_context = {}
                if tryton.context_callback or context:
                    with Transaction().start(database, transaction_user,
                            readonly=True):
                        if tryton.context_callback:
                            transaction_context = tryton.context_callback()
                        transaction_context.update(get_value(context) or {})
                if trytond_version >= (3, 3):
                    retry = config.getint('database', 'retry')
                else:
                    retry = int(config['retry'])

                for count in range(retry, -1, -1):
                    with Transaction().start(database, transaction_user,
                            readonly=is_readonly,
                            context=transaction_context) as transaction:
                        try:
                            result = func(*list(map(instanciate, args)),
                                **dict((n, instanciate(v))
                                    for n, v in kwargs.items()))
                            if (hasattr(transaction, 'cursor')
                                    and not is_readonly):
                                transaction.cursor.commit()
                        except DatabaseOperationalError:
                            if hasattr(transaction, 'cursor'):
                                transaction.cursor.rollback()
                            if count and not is_readonly:
                                continue
                            raise
                        except Exception as e:
                            if hasattr(transaction, 'cursor'):
                                transaction.cursor.rollback()
                            if isinstance(e, (
                                        UserError,
                                        UserWarning,
                                        ConcurrencyException)):
                                raise BadRequest(e.message)
                            raise
                        if trytond_version >= (3, 3):
                            Cache.resets(database)
                    if trytond_version < (3, 3):
                        Cache.resets(database)
                    return result
            return wrapper
        return decorator

tryton_transaction = Tryton.transaction


class _BaseProxy(object):
    pass


class _RecordsProxy(_BaseProxy):
    def __init__(self, model, ids):
        self.model = model
        self.ids = ids

    def __iter__(self):
        return iter(self.ids)

    def __call__(self):
        tryton = current_app.extensions['Tryton']
        Model = tryton.pool.get(self.model)
        return Model.browse(self.ids)


class _RecordProxy(_RecordsProxy):
    def __init__(self, model, id):
        super(_RecordProxy, self).__init__(model, [id])

    def __int__(self):
        return self.ids[0]

    def __call__(self):
        return super(_RecordProxy, self).__call__()[0]


class RecordConverter(BaseConverter):
    """This converter accepts record id of model::

        Rule('/page/<record("res.user"):user>')"""
    regex = r'\d+'

    def __init__(self, map, model):
        super(RecordConverter, self).__init__(map)
        self.model = model

    def to_python(self, value):
        return _RecordProxy(self.model, int(value))

    def to_url(self, value):
        return str(int(value))


class RecordsConverter(BaseConverter):
    """This converter accepts record ids of model::

        Rule('/page/<records("res.user"):users>')"""
    regex = r'\d+(,\d+)*'

    def __init__(self, map, model):
        super(RecordsConverter, self).__init__(map)
        self.model = model

    def to_python(self, value):
        return _RecordsProxy(self.model, list(map(int, value.split(','))))

    def to_url(self, value):
        return ','.join(map(int, value))
