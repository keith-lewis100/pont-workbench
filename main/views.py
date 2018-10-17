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

    def get_display_value(self, key):
        if not key:
            return ""
        entity = key.get()
        return renderers.render_link(self.title_of(entity), url_for_entity(entity))

class IdField:
    def __init__(self):
        self.name = None
        self.label = Label('Id')

class StateField:
    def __init__(self, state_list):
        self.name = 'state_index'
        self.label = Label('State')
        self.state_list = state_list
        
    def get_display_value(self, index):
        state = self.state_list[index]
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
        breadcrumbHtml = renderers.render_breadcrumbs(*breadcrumbs);
        return render_template('entity_list.html',  title=entity_model.name + ' List', breadcrumbs=breadcrumbHtml,
                user=render_user(), entity_table=entity_table, new_button=open_modal, new_dialog=dialog)
        
def action_button(index, action_name, enabled):
    return renderers.render_submit_button(action_name, name='state_index', value=str(index), 
                disabled=not enabled)

class EntityView(View):
    methods = ['GET', 'POST', 'DELETE']

    def __init__(self, entity_model, form_class, *actions):
        self.entity_model = entity_model
        self.form_class = form_class
        self.actions = actions

    def create_menu(self, entity, user):
        buttons = []
        entity_model = self.entity_model
        for index, action_name in self.actions:
            enabled = entity_model.is_transition_allowed(index, entity, user)
            buttons.append(action_button(index, action_name, enabled))
        enabled = entity_model.is_update_allowed(entity, user)
        open_modal = renderers.render_modal_open('Edit', 'm1', enabled)
        return renderers.render_menu('./menu', open_modal, *buttons)

    def get_links(self, entity):
        return []

    def dispatch_request(self, db_id):
        email = users.get_current_user().email()
        user = model.lookup_user_by_email(email)
        entity_model = self.entity_model
        entity = model.lookup_entity(db_id)
        form = self.form_class(request.form, obj=entity)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            entity.put()
            return redirect(request.base_url)    
        title = entity_model.title(entity)
        menu = self.create_menu(entity, user)
        nav = renderers.render_nav(*self.get_links(entity))
        rendered_form = renderers.render_form(form)
        dialog = renderers.render_modal_dialog(rendered_form, 'm1', form.errors)
        
        fields = self.get_fields(form)
        rendered_entity = renderers.render_entity(entity, *fields)
        breadcrumbs = create_breadcrumbs_list(entity)
        breadcrumbHtml = renderers.render_breadcrumbs(*breadcrumbs);
        return render_template('entity.html', title=title, breadcrumbs=breadcrumbHtml, user=render_user(), menu=menu,
                        edit_dialog=dialog, entity=rendered_entity, links=nav)

class MenuView(View):
    methods = ['POST']
    
    def __init__(self, entity_model):
        self.entity_model = entity_model

    def dispatch_request(self, db_id):
        entity = model.lookup_entity(db_id)
        state_index = int(request.form['state_index'])
        self.entity_model.perform_state_change(entity, state_index)
        return redirect(url_for_entity(entity))
