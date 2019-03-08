#_*_ coding: UTF-8 _*_

from html_builder import html
import model
import flask

def url_for_entity(entity):
    key = entity.key
    return flask.url_for('view_%s' % key.kind().lower(), db_id=key.urlsafe())

def get_labels(fields):
    return map(lambda f: f.label, fields)

def display_entity_list(entity_list, fields, no_links=False):
    return map(lambda e: display_entity(e, fields, no_links), entity_list)

def display_entity(entity, fields, no_links=False):
    return map(lambda f: f.get_value(entity, no_links), fields)

def create_accessor(path):
    accessor = None
    for attr in path.split('.'):
        accessor = Accessor(accessor, attr)
    return accessor

class Accessor:
    def __init__(self, entity_accessor, attr):
        self.entity_accessor = entity_accessor
        self.attr = attr

    def __call__(self, entity):
        if self.entity_accessor:
            entity = self.entity_accessor(entity)
        if entity is None:
            return None
        if hasattr(entity, 'get'):
            entity = entity.get() # handle Key
        if self.attr == '#':
            return entity
        if self.attr == '^':
            return entity.key.parent()
        return getattr(entity, self.attr)

def create_readonly_field(name, form_field):
    if hasattr(form_field, 'coerce') and form_field.coerce == model.create_key:
        return ReadOnlyKeyField(name, form_field.label)
    if hasattr(form_field, 'choices'):
        return ReadOnlySelectField(name, form_field.label, coerce=form_field.coerce, 
                        choices=form_field.choices)
    return ReadOnlyField(name, form_field.label)

class ReadOnlyField(object):
    def __init__(self, path, label=None):
        self.accessor = create_accessor(path)
        self.label = label if label != None else path.split('.')[-1].replace("_", " ").title()
        
    def get_value(self, entity, no_links):
        return unicode(self.accessor(entity))

class ReadOnlySelectField(ReadOnlyField):
    def __init__(self, path, label=None, coerce=unicode, choices=[]):
        super(ReadOnlySelectField, self).__init__(path, label)
        self.choices = choices
        self.coerce = coerce

    def get_value(self, entity, no_links):
        property = self.accessor(entity)
        for value, label in self.choices:
            if self.coerce(value) == property:
                return label
        return ""

class ReadOnlyKeyField(ReadOnlyField):
    def __init__(self, path, label=None, title_of=lambda e : e.name):
        super(ReadOnlyKeyField, self).__init__(path, label)
        self.title_of = title_of
        self.wide = False
        
    def get_value(self, entity, no_links):
        key = self.accessor(entity)
        if not key:
            return ""
        target = key.get()
        title = self.title_of(target)
        if no_links:
            return title
        return html.a(self.title_of(target), href=url_for_entity(target))

class StateField(ReadOnlyField):
    def __init__(self, *state_names):
        super(StateField, self).__init__('state_index', 'State')
        self.state_names = state_names

    def get_value(self, entity, no_links):
        state = entity.state_index
        if state == None:
            return "None"
        return self.state_names[state]

class DateField(ReadOnlyField):
    def __init__(self, path, label=None, format='%Y-%m-%d %H:%M:%S'):
        super(DateField, self).__init__(path, label)
        self.format = format

    def get_value(self, entity, no_links):
        date = self.accessor(entity)
        return date.strftime(self.format)

class LiteralField:
    def __init__(self, value, label):
        self.value = value
        self.label = label

    def get_value(self, entity, no_links):
        return self.value
        
class ExchangeCurrencyField(ReadOnlyField):
    def __init__(self, path, label=None):
        super(ExchangeCurrencyField, self).__init__(path, label)

    def get_value(self, entity, no_links):
        payment = self.accessor(entity)
        if payment is None or payment.transfer is None:
            return ""
        transfer = payment.transfer.get()
        if transfer.exchange_rate is None:
            return ""
        requested_amount = payment.amount.value
        if payment.amount.currency == 'sterling':
            sterling = requested_amount
            shillings = int(requested_amount * transfer.exchange_rate)
        if payment.amount.currency == 'ugx':
            sterling = int(requested_amount / transfer.exchange_rate)
            shillings = requested_amount
        return u"£{:,}".format(sterling) + "/" + u"{:,}".format(shillings) + ' Ush'
