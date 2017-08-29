import wtforms
from wtforms.widgets import html_params, HTMLString

def render_field(field):
    html = [field.label(), field(class_="u-full-width"), '<span class="error">']
    for error in field.errors:
        html.append(error)
    html.append('</span>')
    return HTMLString(''.join(html))


def form_field_widget(form_field, **kwargs):
    html = ['<div %s>' % html_params(**kwargs)]
    for field in form_field:
        html.append(render_field(field))
    html.append('</div>')
    return HTMLString(''.join(html))

class ViewModel(wtforms.Form):
    def render_fields(self, field_names):
        html = []
        for name in field_names:
            field = self[name]
            html.append(render_field(field))
        return HTMLString(''.join(html))
