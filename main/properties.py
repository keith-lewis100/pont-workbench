#_*_ coding: UTF-8 _*_

from html_builder import html
import data_models
import flask

def url_for_entity(entity):
    key = entity.key
    return flask.url_for('view_%s' % key.kind().lower(), db_id=key.urlsafe())

def get_labels(fields):
    return [f.label for f in fields]

def display_entity_list(entity_list, fields, no_links=False):
    return [display_entity(e, fields, no_links) for e in entity_list]

def display_entity(entity, fields, no_links=False):
    return [f.str_for(entity, no_links) for f in fields]

def create_readonly_field(name, form_field):
    if hasattr(form_field, 'coerce') and form_field.coerce == data_models.create_key:
        return KeyProperty(name, form_field.label)
    if hasattr(form_field, 'choices'):
        return SelectProperty(name, form_field.label, coerce=form_field.coerce,
                        choices=form_field.choices)
    if form_field.type == 'DateField':
        return DateProperty(name, form_field.label, form_field.format)
    return StringProperty(name, form_field.label)

class Property(object):
    def __init__(self, attr, label=None):
        self.attr = attr
        self.label = label if label is not None else attr.split('.')[-1].replace("_", " ").title()

    def value_for(self, entity):
        if callable(self.attr):
            return self.attr(entity)
        return getattr(entity, self.attr)

class StringProperty(Property):
    def str_for(self, entity, no_links):
        return unicode(self.value_for(entity))

class SelectProperty(Property):
    def __init__(self, attr, label=None, coerce=unicode, choices=[]):
        super(SelectProperty, self).__init__(attr, label)
        self.choices = choices
        self.coerce = coerce

    def str_for(self, entity, no_links):
        property = self.value_for(entity)
        for value, label in self.choices:
            if self.coerce(value) == property:
                return label
        return ""

class KeyProperty(Property):
    def __init__(self, attr, label=None, title_of=lambda e : e.name):
        super(KeyProperty, self).__init__(attr, label)
        self.title_of = title_of
        
    def str_for(self, entity, no_links):
        key = self.value_for(entity)
        if not key:
            return ""
        target = key.get()
        title = self.title_of(target)
        if no_links:
            return title
        return html.a(self.title_of(target), href=url_for_entity(target))

class DateProperty(Property):
    def __init__(self, attr, label=None, format='%Y-%m-%d %H:%M:%S'):
        super(DateProperty, self).__init__(attr, label)
        self.format = format

    def str_for(self, entity, no_links):
        date = self.value_for(entity)
        return date.strftime(self.format)
        
class ExchangeCurrencyProperty(Property):
    def __init__(self, attr, label=None):
        super(ExchangeCurrencyProperty, self).__init__(attr, label)

    def str_for(self, entity, no_links):
        payment = self.value_for(entity)
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
