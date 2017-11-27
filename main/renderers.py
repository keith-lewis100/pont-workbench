#_*_ coding: UTF-8 _*_

import wtforms
from html_builder import html

class SafeString(unicode):
    def __html__(self):
        return self

def radio_field_widget(field, **kwargs):
    kwargs.setdefault('id', field.id)
    children = []
    for val, label, selected in field.iter_choices():
        children.append(label);
        children.append(render_radio_input(field.name, val, selected))
    return html.div(*children, **kwargs)

def render_radio_input(name, val, selected):
    return html.input(type="radio", name=name, value=val, checked=selected)

def render_field(field):
    elements = []
    elements.append(field.label())
    elements.append(field(class_="u-full-width"))
    if field.errors and not field is wtforms.FormField:
        elements.append(html.span(' '.join(*field.errors), class_="error"))
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

def get_display_value(field, property):
    if hasattr(field, 'get_display_value'):
        return field.get_display_value(property)
    return unicode(property)

def render_entity(entity, *fields):
    rows = []
    numFields = len(fields)
    for x in range(0, numFields, 3):
        cols = []
        for y in range(3):
            if x + y >= numFields:
                break
            field = fields[x + y]
            cols.append(render_property(entity, field))
        rows.append(html.div(*cols, class_="row"))    
    return html.div(*rows)
 
def render_property(entity, field):
    property = getattr(entity, field.name)
    label = html.legend(field.label.text)
    value = get_display_value(field, property)
    return html.div(label, value, class_="four columns")

def render_entity_list(rows, *fields):
    head = render_header(fields)
    body = html.tbody(*rows)
    return html.table(head, body, class_="u-full-width")
    
def render_header(fields):
    children = []
    for field in fields:
        children.append(html.th(field.label.text))
    row = html.tr(*children)
    return html.thead(row)
    
def render_row(entity, url, *fields):
    children = []
    for field in fields:
        property = getattr(entity, field.name)
        value = get_display_value(field, property)
        children.append(html.td(value))
    return html.tr(*children, class_="selectable", 
                   onclick="window.location='%s'" % url)

def render_link(label, url, **kwargs):
    return html.a(label, href=url, **kwargs)
    
def render_submit_button(label, **kwargs):
    return html.button(label, type="submit", **kwargs)

def render_menu(url, *content):
    return html.nav(html.form(*content, method="post", action=url))

def render_nav(*content):
    return html.nav(*content)

def render_breadcrumbs(*content):
    return html.div(*content)

def render_logout(user, url):
    return html.span('Welcome, {}! '.format(user), html.a('log out', href=url, class_="button"))
         
def render_modal_open(legend, id, enabled):
    return html.button(legend, type="button", onclick="openDialog('%s');" % id, disabled=not enabled)
    
def render_modal_dialog(element, id, open=False):
    close = html.span(SafeString("&times;"), class_="close", onclick="closeDialog('%s');" % id)
    content = html.div(close, element, class_="modal-content")
    class_val = "modal"
    if open:
        class_val = "modal modal-open"
    return html.div(content, id=id, class_="%s" % class_val)
