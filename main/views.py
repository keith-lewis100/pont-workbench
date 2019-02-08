#_*_ coding: UTF-8 _*_

from flask import render_template, redirect, request, url_for
from flask.views import View
from google.appengine.api import users

import db
import renderers
import model
import custom_fields

class ReadOnlyField(object):
    def __init__(self, name, label=None):
        self.name = name
        self.label = label if label != None else name.capitalize()
        
    def render_value(self, entity):
        return unicode(getattr(entity, self.name))

    def render(self, entity):
        value = self.render_value(entity)
        legend = renderers.legend(self.label)
        return (legend, value)

class ReadOnlySelectField(ReadOnlyField):
    def __init__(self, name, label, choices, coerce=unicode):
        super(ReadOnlySelectField, self).__init__(name, label)
        self.choices = choices
        self.coerce = coerce

    def render_value(self, entity):
        property = getattr(entity, self.name)
        for value, label in self.choices:
            if self.coerce(value) == property:
                return label
        return ""
        
class ReadOnlyKeyField:
    def __init__(self, name, label, title_of=lambda e : e.name):
        self.name = name
        self.label = label if label != None else name.capitalize()
        self.title_of = title_of
        
    def render_value(self, entity):
        key = getattr(entity, self.name)
        if not key:
            return ""
        target = key.get()
        return self.title_of(target)
        
    def render(self, entity):
        key = getattr(entity, self.name)
        if not key:
            return ""
        target = key.get()
        legend = renderers.legend(self.label)
        link = renderers.render_link(self.title_of(target), url_for_entity(target))
        return (legend, link)

def create_form_field(name, field):
    if hasattr(field, 'coerce') and field.coerce == model.create_key:
        return ReadOnlyKeyField(name, field.label)
    if hasattr(field, 'choices'):
        return ReadOnlySelectField(name, field.label, field.choices, field.coerce)
    return ReadOnlyField(name, field.label)

class StateField(ReadOnlyField):
    def __init__(self, *state_names):
        super(StateField, self).__init__('state_index', 'State')
        self.state_names = state_names

    def render_value(self, entity):
        state = entity.state_index
        if state == None:
            return "None"
        return self.state_names[state]
            
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
    
    def __init__(self, entity_model):
        self.entity_model = entity_model

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
        return render_template('layout.html', title=entity_model.name + ' List', breadcrumbs=breadcrumbHtml, user=render_user(), main=entity_table)

def render_entity_view(title, breadcrumbs, links, buttons, dialogs, entity, fields):
    breadcrumbHtml = renderers.render_div(*breadcrumbs);
    nav = renderers.render_nav(*links)
    menu = renderers.render_menu('.', *buttons)
    grid = renderers.render_entity(entity, *fields)
    main = renderers.render_div(nav, menu, dialogs, grid)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbHtml, user=render_user(), main=main)
    
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
    
    def process_action_button(self, action, entity, user, buttons, dialogs):
        if (request.method == 'POST' and request.form.has_key('action') and
                request.form['action'] == action.name):
            self.entity_model.perform_state_change(entity, action)
            return True

        enabled = action.is_allowed(entity, user)
        button = renderers.render_submit_button(action.label, name='action', value=action.name,
                disabled=not enabled)
        buttons.append(button)
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
          if self.process_action_button(action, entity, user, buttons, dialogs):
            return redirect(request.base_url)
        title = self.entity_model.title(entity)
        breadcrumbs = create_breadcrumbs_list(entity)
        links = self.get_links(entity)
        fields = self.get_fields(form)
        return render_entity_view(title, breadcrumbs, links, buttons, dialogs, entity, fields)
