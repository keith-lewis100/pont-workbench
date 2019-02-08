#_*_ coding: UTF-8 _*_

from wtforms import fields, widgets, validators
import model
from html_builder import html

# check recommended elements in skeleton css framework
def radio_field_widget(field, **kwargs):
    kwargs.setdefault('id', field.id)
    children = []
    for val, label, selected in field.iter_choices():
        children.append(label);
        children.append(html.input(type="radio", name=label, value=val, checked=selected))
    return html.div(*children, **kwargs)

def render_field(field):
    elements = []
    elements.append(field.label())
    elements.append(field(class_="u-full-width"))
    if field.errors and not field is fields.FormField:
        elements.append(html.span(' '.join(field.errors), class_="error"))
    return elements

def render_form(form, **kwargs):
    form_fields = render_fields(form)
    submit = html.input(type="submit", value="Submit", class_="button-primary")
    return html.form(form_fields, submit, method="post", **kwargs)

def render_fields(form):
    elements = []
    for field in form._fields.values():
        elements += render_field(field)
    return elements

def form_field_widget(form_field, **kwargs):
    children = render_fields(form_field)
    return html.div(*children, **kwargs)

def set_field_choices(field, entity_list):
    choices = map(lambda e: (e.key.urlsafe(), e.name), entity_list)
    if field.flags.optional:
        choices = [(None, "")] + choices
    field.choices=choices
