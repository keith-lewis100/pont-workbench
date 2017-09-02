import wtforms
from html_builder import html
import logging

def radio_field_widget(field, **kwargs):
    kwargs.setdefault('id', field.id)
    children = []
    for val, label, selected in field.iter_choices():
        children.append(label);
        children.append(render_radio_input(field.name, val, selected))
    return html.div(*children, **kwargs)

def render_radio_input(name, val, selected):
    return html.input(type="radio", name=name, value=val, checked=selected)

def render_field(field, elements):
    elements.append(field.label())
    elements.append(field(class_="u-full-width"))
    if field.errors:
        elements.append(html.span(*field.errors, class_="error"))

def form_field_widget(form_field, **kwargs):
    return form_field.render_fields(None, **kwargs)

def get_display_value(field, property):
    if hasattr(field, 'iter_choices'):
        field.data = property
        for val, label, selected in field.iter_choices():
            if selected:
                return label
        field.data = None
    return unicode(property) # TODO: handle SelectField etc

def render_button(label, url):
    return html.a(label, href=url, class_="button button-primary")

def url_for_key(key):
    result = ""
    for kind, id in key.pairs():
        result += '/%s/%s' % (kind.lower(), id)
    return result
    
class EntityRenderer(wtforms.Form):
    def render_fields(self, field_names=None, **kwargs):
        children = []
        if field_names is None:
            field_names = self._fields.keys()
        for name in field_names:
            field = self[name]
            render_field(field, children)
        return html.div(*children, **kwargs)
 
    def render_entity_list(self, field_names, entity_list):
        if field_names is None:
            field_names = self._fields.keys()
        head = self.render_header(field_names)
        rows = []
        for entity in entity_list:
            rows.append(self.render_row(field_names, entity))
        body = html.tbody(*rows)
        return html.table(head, body, class_="u-full-width")
        
    def render_header(self, field_names):
        children = []
        for name in field_names:
            field = self[name]
            children.append(html.th(field.label.text))
        row = html.tr(*children)
        return html.thead(row)
        
    def render_row(self, field_names, entity):
        children = []
        for name in field_names:
            field = self[name]
            property = getattr(entity, name)
            value = get_display_value(field, property)
            children.append(html.td(value))
        url = url_for_key(entity.key)
        return html.tr(*children, class_="selectable", 
                       onclick="window.location='%s'" % url)
 
    def render_entity(self, field_names, entity):
        if field_names is None:
            field_names = self._fields.keys()
        children = []
        for name in field_names:
            field = self[name]
            property = getattr(entity, name)
            children.append(html.legend(field.label.text))
            value = get_display_value(field, property)
            children.append(value)
        return html.div(*children)
