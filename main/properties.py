#_*_ coding: UTF-8 _*_

import logging
from html_builder import html
import data_models
from urls import url_for_entity

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
        options = [(form_field.coerce(val), label) for val, label in form_field.choices]
        return SelectProperty(name, form_field.label, options)
    if form_field.type == 'DateField':
        return DateProperty(name, form_field.label, form_field.format)
    return StringProperty(name, form_field.label)

class Property(object):
    def __init__(self, attr, label=None):
        self.attr = attr
        self.label = label if label is not None else attr.split('.')[-1].replace("_", " ").title()

    def value_for(self, entity):
        if callable(self.attr):
            try:
                return self.attr(entity)
            except AttributeError:
                logging.exception("Unable to evaluate property %s", self.label)
                return ""
        return getattr(entity, self.attr)

class StringProperty(Property):
    def str_for(self, entity, no_links):
        return unicode(self.value_for(entity))

class SelectProperty(Property):
    def __init__(self, attr, label=None, options=[]):
        super(SelectProperty, self).__init__(attr, label)
        self.option_map = dict(options)

    def str_for(self, entity, no_links):
        prop = self.value_for(entity)
        return self.option_map.get(prop, "")

class KeyProperty(Property):
    def __init__(self, attr, label=None, title_of=lambda e : e.name):
        super(KeyProperty, self).__init__(attr, label)
        self.title_of = title_of
        
    def str_for(self, entity, no_links):
        key = self.value_for(entity)
        if not key:
            return ""
        target = key.get()
        if not target:
            return ""
        title = self.title_of(target)
        if no_links:
            return title
        return html.a(title, href=url_for_entity(target))

class DateProperty(Property):
    def __init__(self, attr, label=None, format='%Y-%m-%d %H:%M:%S'):
        super(DateProperty, self).__init__(attr, label)
        self.format = format

    def str_for(self, entity, no_links):
        date = self.value_for(entity)
        if date is None:
            return ""
        return date.strftime(self.format)
