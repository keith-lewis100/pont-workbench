
from wtforms.widgets import html_params, HTMLString

"""
  Renders a list of fields as sequence of fields each wrapped in its label
  This is used for fields which encapsulate many inner fields as subfields.
  The widget will try to iterate the field to get access to the subfields and
  call them to render them.
"""
def spanningLabelsWidget(field, **kwargs):
    html = ['<div %s>' % html_params(**kwargs)]
    for subfield in field:
        html.append('<label><span class="label-body">%s</span>%s</label>' % (subfield.label.text, subfield()))
    html.append('</div>')
    return HTMLString(''.join(html))

def renderField(field, **kwargs):
    html = [field.label(), field(), '<span class="error">']
    for error in field.errors:
      html.append(error)
    html.append('</span>')
    return HTMLString(''.join(html))

def renderForm(form, **kwargs):
    html = ['<div %s>' % html_params(**kwargs)]
    for field in form:
        html.append(renderField(field))
    html.append('</div>')
    return HTMLString(''.join(html))
