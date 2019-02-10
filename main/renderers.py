#_*_ coding: UTF-8 _*_

import wtforms
from html_builder import html

class SafeString(unicode):
    def __html__(self):
        return self

def render_grid(obj, items):
    rows = []
    numItems = len(items)
    for x in range(0, numItems, 3):
        cols = []
        for y in range(3):
            if x + y >= numItems:
                break
            item = items[x + y]
            col = html.div(item.render(obj), class_="four columns")
            cols.append(col)
        rows.append(html.div(*cols, class_="row"))    
    return rows

def legend(label):
    return html.legend(label)

def render_table(object_list, url_for_object, *columns):
    head = render_header(*columns)
    rows = []
    for obj in object_list:
        url = url_for_object(obj)
        rows.append(render_row(obj, url, *columns))
    body = html.tbody(*rows)
    return html.table(head, body, class_="u-full-width")
    
def render_header(*columns):
    children = []
    for column in columns:
        children.append(html.th(column.label))
    return html.thead(html.tr(*children))
    
def render_row(obj, url, *columns):
    children = []
    for column in columns:
        value = column.render_value(obj)
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
