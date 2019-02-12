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
            
        rendered_form = custom_fields.render_form(form)
        enabled = entity_model.is_create_allowed(parent, user)
        open_modal = renderers.render_modal_open('New', 'm1', enabled)
        dialog = renderers.render_modal_dialog(rendered_form, 'm1', form.errors)
        entity_table = self.render_entities(parent, form)
        breadcrumbs = create_breadcrumbs(parent)
        breadcrumbHtml = renderers.render_div(*breadcrumbs);
        main = renderers.render_div(open_modal, dialog, entity_table)
        return render_template('layout.html', title=entity_model.name + ' List', breadcrumbs=breadcrumbHtml, user=render_user(), main=main)

def render_view(title, breadcrumbs, content, links=[], buttons=[], dialogs=[]):
    breadcrumbHtml = renderers.render_div(*breadcrumbs);
    nav = renderers.render_nav(*links)
    menu = renderers.render_menu(*buttons)
    main = renderers.render_div(nav, menu, dialogs, content)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbHtml, user=render_user(), main=main)

def process_action_button(action, entity, user, buttons, dialogs=[]):
    enabled = action.is_allowed(entity, user)
    if (request.method == 'POST' and request.form.has_key('action')
             and request.form['action'] == action.name):
        if not enabled:
            raise Exception("Illegal action %s performed" % action.name)
        action.apply_to(entity, user)
        return True

    button = renderers.render_submit_button(action.label, name='action', value=action.name,
            disabled=not enabled)
    buttons.append(button)
    return False
   
class EntityView(View):
    methods = ['GET', 'POST', 'DELETE']

    def __init__(self, entity_model, *actions):
        self.entity_model = entity_model
        self.actions = actions

    def get_links(self, entity):
        return []
        
    def process_edit_button(self, form, entity, user, buttons, dialogs):
        if request.method == 'POST' and not request.form.has_key('action') and form.validate():
            form.populate_obj(entity)
            entity.put()
            return True
        enabled = self.entity_model.is_update_allowed(entity, user)
        button = renderers.render_modal_open('Edit', 'd-edit', enabled)
        rendered_form = custom_fields.render_form(form)
        dialog = renderers.render_modal_dialog(rendered_form, 'd-edit', form.errors)
        buttons.append(button)
        dialogs.append(dialog)
        return False

    def dispatch_request(self, db_id):
        email = users.get_current_user().email()
        user = model.lookup_user_by_email(email)
        entity = model.lookup_entity(db_id)
        form = self.create_form(request.form, entity)
        buttons = []
        dialogs = []
        if self.process_edit_button(form, entity, user, buttons, dialogs):
            return redirect(request.base_url)    
        for action in self.actions:
          if process_action_button(action, entity, user, buttons, dialogs):
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
        return render_view(title, breadcrumbs, grid, links, buttons, dialogs)
