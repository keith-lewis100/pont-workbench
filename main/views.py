#_*_ coding: UTF-8 _*_

from flask import render_template, redirect, request, url_for
from flask.views import View
from google.appengine.api import users

import db
import renderers
import model
import custom_fields
import readonly_fields

def url_for_entity(entity):
    key = entity.key
    return url_for('view_%s' % key.kind().lower(), db_id=key.urlsafe())

def url_for_list(kind, parent):
    db_id = None
    if parent:
        db_id = parent.key.urlsafe()
    return url_for('view_%s_list' % kind.lower(), db_id=db_id)

def current_user():
    email = users.get_current_user().email()
    return model.lookup_user_by_email(email)

def render_user():
    email = users.get_current_user().email()
    user = model.lookup_user_by_email(email)
    logout_url = users.create_logout_url('/')
    return renderers.render_logout(user.name, logout_url)

def create_breadcrumbs(entity):
    if entity is None:
        return [renderers.render_link('Dashboard', '/')]
    listBreadcrumbs = create_breadcrumbs_list(entity)
    return listBreadcrumbs + [" / ", renderers.render_link(entity.name, url_for_entity(entity))]

def create_breadcrumbs_list(entity):
    kind = entity.key.kind()
    parent = model.get_parent(entity)
    breadcrumbs = create_breadcrumbs(parent)
    return breadcrumbs + [" / ", renderers.render_link(kind + " List", url_for_list(kind, parent))]

class ListView(View):
    methods = ['GET', 'POST']
    
    def __init__(self, name, create_action):
        self.name = name
        self.create_action = create_action

    def render_entities(self, parent, form):
        entity_list = self.load_entities(parent)
        fields = self.get_fields(form)
        return readonly_fields.render_table(entity_list, fields)

    def dispatch_request(self, db_id=None):
        email = users.get_current_user().email()
        user = model.lookup_user_by_email(email)
        parent = model.lookup_entity(db_id)
        entity = self.create_entity(parent)
        form = self.create_form(request.form, entity)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            self.create_action.apply_to(entity, user)
            self.create_action.audit(entity, user)
            return redirect(request.base_url)
        
        enabled = self.create_action.is_allowed(parent, user)
        new_button = custom_fields.render_dialog_button('New', 'm1', form, enabled)
        entity_table = self.render_entities(parent, form)
        breadcrumbs = create_breadcrumbs(parent)
        return render_view(self.name + ' List', breadcrumbs, entity_table, buttons=[new_button])

def render_view(title, breadcrumbs, content, links=[], buttons=[]):
    breadcrumbHtml = renderers.render_div(*breadcrumbs);
    nav = renderers.render_nav(*links)
    menu = renderers.render_nav(*buttons)
    main = renderers.render_div(nav, menu, content)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbHtml, user=render_user(), main=main)

def process_action_button(action, entity, user, buttons):
    enabled = action.is_allowed(entity, user)
    button = renderers.render_submit_button(action.label, name='action', value=action.name,
            disabled=not enabled)
    buttons.append(button)
    if (request.method == 'POST' and request.form.has_key('action')
             and request.form['action'] == action.name):
        if not enabled:
            raise Exception("Illegal action %s was performed" % action.name)
        return True

    return False
 
def process_edit_button(action, form, entity, user, buttons):
    if request.method == 'POST' and not request.form.has_key('action') and form.validate():
        form.populate_obj(entity)
        return True
    enabled = action.is_allowed(entity, user)
    edit_button = custom_fields.render_dialog_button(action.label, 'd-edit', form, enabled)
    buttons.append(edit_button)
    return False

audit_fields = [
    readonly_fields.DateField('timestamp'),
    readonly_fields.ReadOnlyField('message'),
    readonly_fields.ReadOnlyField('user.name', 'User')
]

def render_entity_history(key):
    audit_list = db.AuditRecord.query(db.AuditRecord.entity == key).order(-db.AuditRecord.timestamp
                      ).iter(limit = 20)
    sub_heading = renderers.sub_heading('Activity Log')
    table = readonly_fields.render_table(audit_list, audit_fields, selectable=False)
    return (sub_heading, table)

class EntityView(View):
    methods = ['GET', 'POST', 'DELETE']

    def __init__(self, update_action, *actions):
        self.update_action = update_action
        self.actions = actions

    def get_links(self, entity):
        return []
        
    def dispatch_request(self, db_id):
        email = users.get_current_user().email()
        user = model.lookup_user_by_email(email)
        entity = model.lookup_entity(db_id)
        form = self.create_form(request.form, entity)
        buttons = []
        if process_edit_button(self.update_action, form, entity, user, buttons):
            self.update_action.apply_to(entity, user)
            self.update_action.audit(entity, user)
            return redirect(request.base_url)    
        for action in self.actions:
          if process_action_button(action, entity, user, buttons):
            action.apply_to(entity, user)
            action.audit(entity, user)
            return redirect(request.base_url)
        title = self.title(entity)
        breadcrumbs = create_breadcrumbs_list(entity)
        links = self.get_links(entity)
        fields = self.get_fields(form)
        wide_items = []
        if fields[-1].wide:
            last = fields[-1].render(entity)
            wide_items = [renderers.render_div(last, class_="u-full-width")]
            fields = fields[:-1]
        grid = renderers.render_grid(entity, fields) + wide_items
        history = render_entity_history(entity.key)
        return render_view(title, breadcrumbs, (grid, history), links, buttons)
