#_*_ coding: UTF-8 _*_

from wtforms import widgets, Form, FormField, IntegerField, SelectFieldBase, validators
from html_builder import html
import renderers

# check recommended elements in skeleton css framework
def radio_field_widget(field, **kwargs):
    kwargs.setdefault('id', field.id)
    children = []
    for val, label, selected in field.iter_choices():
        children.append(label);
        children.append(html.input(type="radio", name=field.name, value=val, checked=selected))
    return html.div(*children, **kwargs)

def render_field(field):
    elements = [field.label(), field(class_="u-full-width")]
    if field.errors and not field is FormField:
        elements.append(html.span(' '.join(field.errors), class_="error"))
    return elements

def render_fields(form):
    return map(render_field, form._fields.values())

def render_dialog_button(label, action, form, enabled=True):
    id = 'm-' + action
    form_fields = render_fields(form)
    dialog = renderers.render_modal_dialog(form_fields, id, action, form.errors)
    button = renderers.render_modal_open(label, id, disabled=not enabled)
    return (dialog, button)

def form_field_widget(form_field, **kwargs):
    children = render_fields(form_field)
    return html.div(*children, **kwargs)

def set_field_choices(field, entity_list):
    choices = [(e.key.urlsafe(), e.name) for e in entity_list]
    if field.flags.optional:
        choices = [(None, "")] + choices
    field.choices=choices

class SelectField(SelectFieldBase):
    widget = widgets.Select()

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

class MoneyForm(Form):
    currency = SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=radio_field_widget, default='sterling')
    value = IntegerField(validators=[validators.NumberRange(min=10)])

