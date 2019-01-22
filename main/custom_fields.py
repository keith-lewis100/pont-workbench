#_*_ coding: UTF-8 _*_

from wtforms import fields, widgets

class KeyPropertyField(fields.SelectFieldBase):
    widget = widgets.Select()

    def __init__(self, label=None, validators=None, query=None, title_of=lambda e: e.name, **kwargs):
        super(KeyPropertyField, self).__init__(label, validators, **kwargs)
        self.query = query
        self.title_of = title_of
        
    def iter_choices(self):
        entities = self.query.fetch()
        if self.flags.optional:
            yield None, "", self.data == None
        
        for entity in entities:
            val = entity.key.urlsafe()
            name = self.title_of(entity)
            selected = self.data and val == self.data.urlsafe()
            yield val, name, selected

    def process_formdata(self, valuelist):
        if valuelist:
            val = valuelist[0]
            entities = self.query.fetch()
            
            for entity in entities:
                if entity.key.urlsafe() == val:
                    self.data = entity.key

    def get_display_value(self, key):
        if key is None:
            return ""
        entity = key.get()
        return self.title_of(entity)

class SelectField(fields.SelectField):
    def get_display_value(self, property):
        for value, label in self.choices:
            if self.coerce(value) == property:
                return label
        return ""
