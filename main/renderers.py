#_*_ coding: UTF-8 _*_

import wtforms
from html_builder import html

class SafeString(unicode):
    def __html__(self):
        return self

def render_grid(values, labels, num_wide=0):
    rows = []
    numItems = len(values) - num_wide
    for x in range(0, numItems, 3):
        cols = []
        for y in range(3):
            index = x + y
            if index >= numItems:
                break
            value = values[index]
            legend = html.legend(labels[index])
            col = html.div(legend, value, class_="four columns")
            cols.append(col)
        rows.append(html.div(*cols, class_="row"))
    for i in range(numItems, len(values)):
        value = values[i]
        legend = html.legend(labels[i])
        rows.append(html.div(legend, value,  class_="u-full-width"))
    return html.div(rows)

def render_single_column(values, labels):
    rows = []
    for i in range(0, len(values)):
        legend = html.b(labels[i] + ": ")
        rows.append(html.div(legend, values[i]))
    return html.div(rows)

def render_table(column_headers, grid, url_list):
    header = render_header(column_headers)
    if url_list:
        rows = map(render_row, grid, url_list)
    else:
        rows = map(render_row, grid)
    return html.table(html.thead(header), html.tbody(*rows), width="100%")

def render_header(column_headers):
    children = map(html.th, column_headers)
    return html.tr(*children)

def render_row(row, url=None):
    children = map(html.td, row)
    if not url:
        return html.tr(*children)
    return html.tr(*children, class_="selectable", onclick="window.location='%s'" % url)

def render_link(label, url, **kwargs):
    return html.a(label, href=url, **kwargs)
    
def render_submit_button(label, **kwargs):
    button = html.button(label, type="submit", **kwargs)
    return ('\n', html.form(button, method="post"))

def render_div(*content, **kwargs):
    return html.div(*content, **kwargs)

def render_nav(*content, **kwargs):
    return html.nav(*content, **kwargs)

def render_logout(user, url):
    return html.span('Welcome, {}! '.format(user), html.a('log out', href=url, class_="button"))
         
def render_modal_open(legend, id, **kwargs):
    button = html.button(legend, type="button", onclick="openDialog('%s');" % id, **kwargs)
    return html.form(button, method="post")

def render_modal_dialog(form_fields, id, action, open=False):
    hidden = html.input(type="hidden", name="_action", value=action)
    submit = html.input(type="submit", value="Submit", class_="button-primary")
    form = html.form(form_fields, hidden, submit, method="post")
    close = html.span(SafeString("&times;"), class_="close", onclick="closeDialog('%s');" % id)
    content = html.div(close, form, class_="modal-content")
    class_val = "modal"
    if open:
        class_val = "modal modal-open"
    return html.div(content, id=id, class_=class_val)

def sub_heading(heading):
    return (html.br(), html.h3(heading))

def render_errors(errors):
    error_list = [html.div(error, class_='error') for error in errors]
    return html.div(*error_list)
