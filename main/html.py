
from wtforms.widgets import html_params, HTMLString

def render_radio_field(field, **kwargs):
    kwargs.setdefault('id', field.id)
    html = ['<div %s>' % html_params(**kwargs)]
    for val, label, selected in field.iter_choices():
        html.append(label);
        html.append(render_radio_input(field.name, val, selected))
    html.append('</div>')
    return HTMLString(''.join(html))

def render_radio_input(name, val, selected):
    return HTMLString('<input type="radio" %s>' % html_params(name=name, value=val, checked=selected))
