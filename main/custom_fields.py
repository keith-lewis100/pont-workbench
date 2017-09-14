#_*_ coding: UTF-8 _*_
from wtforms import fields, widgets

class KeyPropertyField(fields.SelectFieldBase):
    widget = widgets.Select()

    def __init__(self, label=None, validators=None, query=None, name_attr='name', **kwargs):
        super(KeyPropertyField, self).__init__(label, validators, **kwargs)
        self.query = query
        self.name_attr = name_attr
        
    def iter_choices(self):
        entities = self.query.fetch()
        
        for entity in entities:
            val = entity.key.urlsafe()
            name = getattr(entity, self.name_attr)
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
        return getattr(entity, self.name_attr)