#_*_ coding: UTF-8 _*_

from html_builder import html
import model
import views

def create_readonly_field(name, form_field):
    if hasattr(form_field, 'coerce') and form_field.coerce == model.create_key:
        return ReadOnlyKeyField(name, form_field.label)
    if hasattr(form_field, 'choices'):
        return ReadOnlySelectField(name, form_field.label, coerce=form_field.coerce, 
                        choices=form_field.choices)
    return ReadOnlyField(name, form_field.label, form_field.type == 'TextAreaField')

class ReadOnlyField(object):
    def __init__(self, name, label=None, wide=False):
        self.name = name
        self.label = label if label != None else name.replace("_", " ").title()
        self.wide = wide
        
    def render_value(self, entity):
        return unicode(getattr(entity, self.name))

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
        property = getattr(entity, self.name)
        for value, label in self.choices:
            if self.coerce(value) == property:
                return label
        return ""
        
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
        link = html.a(self.title_of(target), href=views.url_for_entity(target))
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
            
