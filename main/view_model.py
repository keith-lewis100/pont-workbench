import wtforms
from html_builder import html

def render_field(field, elements):
    elements.append(field.label())
    elements.append(field(class_="u-full-width"))
    if field.errors:
        elements.append(html.span(*field.errors, class_="error"))

def form_field_widget(form_field, **kwargs):
    return form_field.render_fields(None, **kwargs)

class ViewModel(wtforms.Form):
    def render_fields(self, field_names, **kwargs):
        children = []
        if field_names is None:
            field_names = self._fields.keys()
        for name in field_names:
            field = self[name]
            render_field(field, children)
        return html.div(*children, **kwargs)
