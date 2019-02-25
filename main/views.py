#_*_ coding: UTF-8 _*_

from flask import render_template, redirect, request, url_for
from flask.views import View
from google.appengine.api import users

import renderers
import model
import custom_fields

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
    
    def __init__(self, entity_model):
        self.entity_model = entity_model

    def render_entities(self, parent, form):
        entity_list = self.entity_model.load_entities(parent)
        fields = self.get_fields(form)
        return renderers.render_table(entity_list, url_for_entity, *fields)

    def dispatch_request(self, db_id=None):
        email = users.get_current_user().email()
        user = model.lookup_user_by_email(email)
        entity_model = self.entity_model
        parent = model.lookup_entity(db_id)
        entity = entity_model.create_entity(parent)
        form = self.create_form(request.form, entity)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            entity_model.perform_create(entity, user)
            return redirect(request.base_url)
            
        enabled = entity_model.is_create_allowed(parent, user)
        new_button = custom_fields.render_dialog_button('New', 'm1', form, enabled)
        entity_table = self.render_entities(parent, form)
        breadcrumbs = create_breadcrumbs(parent)
        return render_view(entity_model.name + ' List', breadcrumbs, entity_table, buttons=[new_button])

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
 
class EntityView(View):
    methods = ['GET', 'POST', 'DELETE']

    def __init__(self, entity_model, *actions):
        self.entity_model = entity_model
        self.actions = actions

    def get_links(self, entity):
        return []
        
    def dispatch_request(self, db_id):
        email = users.get_current_user().email()
        user = model.lookup_user_by_email(email)
        entity = model.lookup_entity(db_id)
        form = self.create_form(request.form, entity)
        buttons = []
        update_action = self.entity_model.get_update_action()
        if process_edit_button(update_action, form, entity, user, buttons):
            entity.put()
            return redirect(request.base_url)    
        for action in self.actions:
          if process_action_button(action, entity, user, buttons):
            action.apply_to(entity)
            return redirect(request.base_url)
        title = self.entity_model.title(entity)
        breadcrumbs = create_breadcrumbs_list(entity)
        links = self.get_links(entity)
        fields = self.get_fields(form)
        wide_items = []
        if fields[-1].wide:
            last = fields[-1].render(entity)
            wide_items = [renderers.render_div(last, class_="u-full-width")]
            fields = fields[:-1]
        grid = renderers.render_grid(entity, fields) + wide_items
        return render_view(title, breadcrumbs, grid, links, buttons)
