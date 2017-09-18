import wtforms
from html_builder import html

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
        
def render_fields(*fields, **kwargs):
    children = []
    for field in fields:
        children.append(render_field(field))
    return html.div(*children, **kwargs)

def form_field_widget(form_field, **kwargs):
    return render_fields(*form_field._fields.values(), **kwargs)

def get_display_value(field, property):
    if hasattr(field, 'get_display_value'):
        return field.get_display_value(property)
    if hasattr(field, 'iter_choices'): # TODO: use choices and coerce instead
        field.data = property
        for val, label, selected in field.iter_choices():
            if selected:
                return label
        field.data = None
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
    
def render_button(label, type='submit', **kwargs):
    return html.button(label, type=type, **kwargs)

def render_form(*content, **kwargs):
    return html.form(*content, method="post", **kwargs)
    
def render_div(*content, **kwargs):
    return html.div(*content, **kwargs)

def url_for_key(key): #TODO: move up to views.py
    return '/%s/%s' % (key.kind().lower(), key.urlsafe())
