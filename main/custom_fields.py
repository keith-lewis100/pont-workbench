#_*_ coding: UTF-8 _*_

import wtforms
from html_builder import html

# check recommended elements in skeleton css framework
def radio_field_widget(field, **kwargs):
    kwargs.setdefault('id', field.id)
    children = []
    for val, label, selected in field.iter_choices():
        children.append(label);
        children.append(html.input(type="radio", name=field.name, value=val, checked=selected))
    return html.div(*children, **kwargs)

def render_field(field):
    elements = []
    elements.append(field.label())
    elements.append(field(class_="u-full-width"))
    if field.errors and not field is wtforms.FormField:
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

class SelectField(wtforms.SelectFieldBase):
    widget = wtforms.widgets.Select()

    def __init__(self, label=None, validators=None, coerce=unicode, choices=None, **kwargs):
        super(SelectField, self).__init__(label, validators, **kwargs)
        self.coerce = coerce
        self.choices = choices

    def iter_choices(self):
        for value, label in self.choices:
            yield (value, label, self.coerce(value) == self.data)

    def process_data(self, data):
        try:
            self.data = data
        except (ValueError, TypeError):
            self.data = None

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = self.coerce(valuelist[0])
            except ValueError:
                raise ValueError(self.gettext('Invalid Choice: could not coerce'))

    def pre_validate(self, form):
        for v, _ in self.choices:
            if self.data == self.coerce(v):
                break
        else:
            raise ValueError(self.gettext('Not a valid choice'))