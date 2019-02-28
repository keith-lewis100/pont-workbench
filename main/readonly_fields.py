#_*_ coding: UTF-8 _*_

from html_builder import html
import model
import flask

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
            key = self.entity_accessor(entity)
            entity = key.get()
        if self.attr == '^':
            return entity.key.parent()
        return getattr(entity, self.attr)

def create_readonly_field(name, form_field):
    if hasattr(form_field, 'coerce') and form_field.coerce == model.create_key:
        return ReadOnlyKeyField(name, form_field.label)
    if hasattr(form_field, 'choices'):
        return ReadOnlySelectField(name, form_field.label, coerce=form_field.coerce, 
                        choices=form_field.choices)
    return ReadOnlyField(name, form_field.label, form_field.type == 'TextAreaField')

class ReadOnlyField(object):
    def __init__(self, path, label=None, wide=False):
        self.accessor = create_accessor(path)
        self.label = label if label != None else path.replace("_", " ").title()
        self.wide = wide
        
    def render_value(self, entity):
        return unicode(self.accessor(entity))

    def render(self, entity):
        value = self.render_value(entity)
        legend = html.legend(self.label)
        return (legend, value)

class ReadOnlySelectField(ReadOnlyField):
    def __init__(self, name, label=None, coerce=unicode, choices=[]):
        super(ReadOnlySelectField, self).__init__(name, label)
        self.choices = choices
        self.coerce = coerce

    def render_value(self, entity):
        property = self.accessor(entity)
        for value, label in self.choices:
            if self.coerce(value) == property:
                return label
        return ""

def url_for_key(key):
    return flask.url_for('view_%s' % key.kind().lower(), db_id=key.urlsafe())

class ReadOnlyKeyField:
    def __init__(self, name, label=None, title_of=lambda e : e.name):
        self.name = name
        self.label = label if label != None else name.replace("_", " ").title()
        self.title_of = title_of
        self.wide = False
        
    def render_value(self, entity):
        key = getattr(entity, self.name)
        if not key:
            return ""
        target = key.get()
        return self.title_of(target)
        
    def render(self, entity):
        key = getattr(entity, self.name)
        if not key:
            return ""
        target = key.get()
        legend = html.legend(self.label)
        link = html.a(self.title_of(target), href=url_for_key(key))
        return (legend, link)

class StateField(ReadOnlyField):
    def __init__(self, *state_names):
        super(StateField, self).__init__('state_index', 'State')
        self.state_names = state_names

    def render_value(self, entity):
        state = entity.state_index
        if state == None:
            return "None"
        return self.state_names[state]
            
