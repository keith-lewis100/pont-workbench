#_*_ coding: UTF-8 _*_

import wtforms
from html_builder import html

class SafeString(unicode):
    def __html__(self):
        return self

def get_display_value(field, entity):
    return field.render_value(entity)

# Rename to render_grid(fields, **kwargs)
# deal with TextAreaField separately
# call render_grid_cell on each field passing kwargs
def render_entity(entity, *fields):
    rows = []
    numFields = len(fields)
    start = 0
    if False:
        first = render_field(fields[0], entity, class_="u-full-width")
        rows.append(html.div(first, class_="row"))
        start = 1
    for x in range(start, numFields, 3):
        cols = []
        for y in range(3):
            if x + y >= numFields:
                break
            field = fields[x + y]
            cols.append(render_field(field, entity))
        rows.append(html.div(*cols, class_="row"))    
    return rows
 
def render_field(field, entity, class_="four columns"):
    content = field.render(entity)
    return html.div(content, class_=class_)

def legend(label):
    return html.legend(label)

# TODO: combine the following 3 methods into a single
# render_table method
# make field class implement render_header and render_table_cell methods
def render_entity_list(rows, *fields):
    head = render_header(fields)
    body = html.tbody(*rows)
    return html.table(head, body, class_="u-full-width")
    
def render_header(fields):
    children = []
    for field in fields:
        children.append(html.th(field.label))
    row = html.tr(*children)
    return html.thead(row)
    
def render_row(entity, url, *fields):
    children = []
    for field in fields:
        value = get_display_value(field, entity)
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

def render_div(*content, **kwargs):
    return html.div(*content, **kwargs)

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

def month_widget(field, **kwargs):
    return html.input(type='month', **kwargs)