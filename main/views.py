#_*_ coding: UTF-8 _*_

from flask import render_template, redirect, request, url_for
from flask.views import View
from google.appengine.api import users

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

def url_for_entity(entity):
    key = entity.key
    return '/%s/%s/' % (key.kind().lower(), key.urlsafe())

def render_user():
    cur_user = users.get_current_user()
    email = cur_user.email()
    user = model.user_by_email(email)
    name = user.name if user else email
    logout_url = users.create_logout_url('/')
    return renderers.render_logout(name, logout_url)

class ListView(View):
    methods = ['GET', 'POST']
        
    def url_for_entity(self, entity):
        return url_for_entity(entity)
    
    def render_entities(self, parent, form):
        entity_list = self.load_entities(parent)
        fields = self.get_fields(form)
        rows = []
        for e in entity_list:
            url = self.url_for_entity(e)
            rows.append(renderers.render_row(e, url, *fields))
        return renderers.render_entity_list(rows, *fields)

    def dispatch_request(self, db_id=None):
        email = users.get_current_user().email()
        user = model.user_by_email(email)
        parent = model.lookup_entity(db_id)
        entity = self.create_entity(parent)
        form = self.formClass(request.form, obj=entity)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            model.perform_create(self.kind, entity, user)
            return redirect(request.base_url)
            
        rendered_form = renderers.render_form(form)
        enabled = model.is_action_allowed(('create', self.kind), parent, user)
        open_modal = renderers.render_modal_open('New', 'm1', enabled)
        dialog = renderers.render_modal_dialog(rendered_form, 'm1', form.errors)
        entity_table = self.render_entities(parent, form)
        return render_template('entity_list.html',  title=self.kind + ' List', user=render_user(),
                entity_table=entity_table, new_button=open_modal, new_dialog=dialog)
        
def action_button(index, action_name, entity, user):
    enabled = model.is_action_allowed(('state-change', index), entity, user)
    return renderers.render_submit_button(action_name, name='new_state', value=str(index), 
                disabled=not enabled)

class EntityView(View):
    methods = ['GET', 'POST']
    
    def create_menu(self, entity, user):
        buttons = []
        for index, action_name in self.actions:
            buttons.append(action_button(index, action_name, entity, user))
        enabled = model.is_action_allowed(('update',), entity, user)
        open_modal = renderers.render_modal_open('Edit', 'm1', enabled)
        return renderers.render_menu('./menu', open_modal, *buttons)

    def create_breadcrumbs(self, entity):
        if entity is None:
            return []
        parent = model.getParent(entity)
        parentBreadcrumbs = self.create_breadcrumbs(parent)
        return parentBreadcrumbs + ["/ ", 
                    renderers.render_link(entity.name, url_for_entity(entity))]

    def dispatch_request(self, db_id):
        email = users.get_current_user().email()
        user = model.user_by_email(email)
        entity = model.lookup_entity(db_id)
        form = self.formClass(request.form, obj=entity)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            model.perform_update(entity)
            return redirect(request.base_url)
            
        title = self.title(entity)
        breadcrumbs = self.create_breadcrumbs(model.getParent(entity))
        menu = self.create_menu(entity, user)
        links = self.get_links(entity)
        rendered_form = renderers.render_form(form)
        dialog = renderers.render_modal_dialog(rendered_form, 'm1', form.errors)
        
        fields = self.get_fields(form)
        rendered_entity = renderers.render_entity(entity, *fields)
        breadcrumbHtml = renderers.render_breadcrumbs(*breadcrumbs);
        return render_template('entity.html', title=title, breadcrumbs=breadcrumbHtml, user=render_user(), menu=menu,
                        edit_dialog=dialog, entity=rendered_entity, links=links)

class MenuView(View):
    methods = ['POST']
    
    def dispatch_request(self, db_id):
        entity = model.lookup_entity(db_id)
        new_state = int(request.form['new_state'])
        model.perform_state_change(new_state, entity)
        return redirect(url_for_entity(entity))
