#_*_ coding: UTF-8 _*_

from flask import render_template, redirect, request, url_for
from flask.views import View
from google.appengine.api import users

import db
import renderers
import model

class Label:
    def __init__(self, text):
        self.text = text

class ReadOnlyField:
    def __init__(self, name, label):
        self.name = name
        self.label = Label(label)

class ReadOnlyKeyField:
    def __init__(self, name, label, title_of=lambda e : e.name):
        self.name = name
        self.label = Label(label)
        self.title_of = title_of

    def get_display_value(self, entity):
        key = getattr(entity, self.name)
        if not key:
            return ""
        target = key.get()
        return renderers.render_link(self.title_of(target), url_for_entity(target))

class StateField:
    def __init__(self, state_list):
        self.label = Label('State')
        self.state_list = state_list
        
    def get_display_value(self, entity):
        state = self.state_list[entity.state_index]
        return state.display_name
            
def url_for_entity(entity):
    key = entity.key
    return url_for('view_%s' % key.kind().lower(), db_id=key.urlsafe())

def url_for_list(kind, parent):
    db_id = None
    if parent:
        db_id = parent.key.urlsafe()
    return url_for('view_%s_list' % kind.lower(), db_id=db_id)

def render_user():
    email = users.get_current_user().email()
    user = model.lookup_user_by_email(email)
    name = user.name if user else email
    logout_url = users.create_logout_url('/')
    return renderers.render_logout(name, logout_url)

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
    
    def __init__(self, entity_model, form_class):
        self.entity_model = entity_model
        self.form_class = form_class

    def render_entities(self, parent, form):
        entity_list = self.entity_model.load_entities(parent)
        fields = self.get_fields(form)
        rows = []
        for e in entity_list:
            url = url_for_entity(e)
            rows.append(renderers.render_row(e, url, *fields))
        return renderers.render_entity_list(rows, *fields)

    def dispatch_request(self, db_id=None):
        email = users.get_current_user().email()
        user = model.lookup_user_by_email(email)
        entity_model = self.entity_model
        parent = model.lookup_entity(db_id)
        entity = entity_model.create_entity(parent)
        form = self.form_class(request.form, obj=entity)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            entity_model.perform_create(entity, user)
            return redirect(request.base_url)
            
        rendered_form = renderers.render_form(form)
        enabled = entity_model.is_create_allowed(parent, user)
        open_modal = renderers.render_modal_open('New', 'm1', enabled)
        dialog = renderers.render_modal_dialog(rendered_form, 'm1', form.errors)
        entity_table = self.render_entities(parent, form)
        breadcrumbs = create_breadcrumbs(parent)
        breadcrumbHtml = renderers.render_div(*breadcrumbs);
        return render_template('entity_list.html',  title=entity_model.name + ' List', breadcrumbs=breadcrumbHtml,
                user=render_user(), entity_table=entity_table, new_button=open_modal, new_dialog=dialog)

class ListViewNoCreate(View):
    methods = ['GET']
    
    def __init__(self, entity_model):
        self.entity_model = entity_model

    def render_entities(self, parent):
        entity_list = self.entity_model.load_entities(parent)
        fields = self.get_fields()
        rows = []
        for e in entity_list:
            url = url_for_entity(e)
            rows.append(renderers.render_row(e, url, *fields))
        return renderers.render_entity_list(rows, *fields)

    def dispatch_request(self, db_id=None):
        email = users.get_current_user().email()
        user = model.lookup_user_by_email(email)
        entity_model = self.entity_model
        parent = model.lookup_entity(db_id)
        entity_table = self.render_entities(parent)
        breadcrumbs = create_breadcrumbs(parent)
        breadcrumbHtml = renderers.render_div(*breadcrumbs);
        return render_template('entity_list.html',  title=entity_model.name + ' List', breadcrumbs=breadcrumbHtml,
                user=render_user(), entity_table=entity_table)

def render_entity_view(title, breadcrumbs, links, buttons, dialogs, entity, fields):
    breadcrumbHtml = renderers.render_div(*breadcrumbs);
    nav = renderers.render_nav(*links)
    menu = renderers.render_menu('.', *buttons)
    grid = renderers.render_entity(entity, *fields)
    main = renderers.render_div(nav, menu, dialogs, grid)
    return render_template('entity.html', title=title, breadcrumbs=breadcrumbHtml, user=render_user(), main=main)
    
class EntityView(View):
    methods = ['GET', 'POST', 'DELETE']

    def __init__(self, entity_model, form_class, *actions):
        self.entity_model = entity_model
        self.form_class = form_class
        self.actions = actions

    def get_links(self, entity):
        return []
        
    def process_edit_button(self, user, form, entity, buttons, dialogs):
        if request.method == 'POST' and not request.form.has_key('action') and form.validate():
            form.populate_obj(entity)
            entity.put()
            return True
        enabled = self.entity_model.is_update_allowed(entity, user)
        button = renderers.render_modal_open('Edit', 'd-edit', enabled)
        rendered_form = renderers.render_form(form)
        dialog = renderers.render_modal_dialog(rendered_form, 'd-edit', form.errors)
        buttons.append(button)
        dialogs.append(dialog)
        return False
    
    def process_action_button(self, action, label, enabled, entity, buttons, dialogs):
        if (request.method == 'POST' and request.form.has_key('action') and
                request.form['action'] == action):
            self.entity_model.perform_state_change(entity, action)
            entity.put()
            return True

        button = renderers.render_submit_button(label, name='action', value=action,
                disabled=not enabled)
        buttons.append(button)
        return False

    def dispatch_request(self, db_id):
        email = users.get_current_user().email()
        user = model.lookup_user_by_email(email)
        entity = model.lookup_entity(db_id)
        form = self.form_class(request.form, obj=entity)
        buttons = []
        dialogs = []
        if self.process_edit_button(user, form, entity, buttons, dialogs):
            return redirect(request.base_url)    
        for action, label in self.actions:
          enabled = self.entity_model.is_action_allowed(action, entity, user)
          if self.process_action_button(action, label, enabled, entity, buttons, dialogs):
            return redirect(request.base_url)
        title = self.entity_model.title(entity)
        breadcrumbs = create_breadcrumbs_list(entity)
        links = self.get_links(entity)
        fields = self.get_fields(form)
        return render_entity_view(title, breadcrumbs, links, buttons, dialogs, entity, fields)

class MenuView(View):
    methods = ['POST']
    
    def __init__(self, entity_model):
        self.entity_model = entity_model

    def dispatch_request(self, db_id):
        entity = model.lookup_entity(db_id)
        action = request.form['action']
        self.entity_model.perform_state_change(entity, action)
        entity.put()
        return redirect(url_for_entity(entity))
