#_*_ coding: UTF-8 _*_

from flask import render_template, redirect, request, url_for
from flask.views import View
from google.appengine.api import users

import db
import renderers
import data_models
import custom_fields
import properties

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
    user = data_models.lookup_user_by_email(email)
    logout_url = users.create_logout_url('/')
    return renderers.render_logout(user.name, logout_url)

def create_breadcrumbs(entity):
    if entity is None:
        return [renderers.render_link('Dashboard', '/')]
    listBreadcrumbs = create_breadcrumbs_list(entity)
    return listBreadcrumbs + [" / ", renderers.render_link(entity.name, url_for_entity(entity))]

def create_breadcrumbs_list(entity):
    kind = entity.key.kind()
    parent = data_models.get_parent(entity)
    breadcrumbs = create_breadcrumbs(parent)
    return breadcrumbs + [" / ", renderers.render_link(kind + " List", url_for_list(kind, parent))]

def render_entity(entity, fields, num_wide=0):
    values = properties.display_entity(entity, fields)
    labels = properties.get_labels(fields)
    return renderers.render_grid(values, labels, num_wide)

def render_entity_list(entity_list, fields, selectable=True):
    column_headers = properties.get_labels(fields)
    grid = properties.display_entity_list(entity_list, fields, selectable)
    url_list = map(url_for_entity, entity_list) if selectable else None
    return renderers.render_table(column_headers, grid, url_list)

def render_link(kind, label, parent=None):
    url = url_for_entity_list(kind, parent)
    return renderers.render_link(label, url, class_="button")

audit_fields = [
    properties.DateProperty('timestamp'),
    properties.StringProperty('message'),
    properties.KeyProperty('user')
]

def render_entity_history(key):
    audit_list = db.AuditRecord.query(db.AuditRecord.entity == key).order(-db.AuditRecord.timestamp
                      ).iter(limit = 20)
    sub_heading = renderers.sub_heading('Activity Log')
    table = render_entity_list(audit_list, audit_fields, selectable=False)
    return (sub_heading, table)

class Action(object):
    def __init__(self, name, label, required_role, has_form=True):
        self.name = name
        self.label = label
        self.required_role = required_role
        self.has_form = has_form

    def is_allowed(self, model):
        types = model.get_role_types()
        if not self.required_role in types:
            return False
        return True

    def process_input(self, model):
        enabled = self.is_allowed(model)
        assert enabled
        form = model.get_form(self.name)
        if form and not form.validate():
            return False
        method = getattr(model, 'perform_' + self.name)
        method()
        return True

    def render(self, model):
        enabled = self.is_allowed(model)
        if self.has_form:
            form = model.get_form(self.name)
            return custom_fields.render_dialog_button(self.label, self.name, form, enabled)
        return renderers.render_submit_button(self.label, name='_action', value=self.name,
                disabled=not enabled)

class StateAction(Action):
    def __init__(self, name, label, required_role, allowed_states, has_form=False):
        super(StateAction, self).__init__(name, label, required_role, has_form)
        self.allowed_states = allowed_states

    def is_allowed(self, model):
        if not super(StateAction, self).is_allowed(model):
            return False
        state = model.get_state()
        return state in self.allowed_states

class CreateAction(Action):
   def __init__(self, required_role):
        super(CreateAction, self).__init__('create', 'New', required_role)

def handle_post(model, action_list):
    action_name = request.form['_action']
    for action in action_list:
        if action.name == action_name:
            return action.process_input(model)
    raise NotImplemented        

def view_entity_list(model, title, property_list, create_action):
    if request.method == 'POST' and create_action.process_input(model):
        return redirect(request.base_url)
    entity_table = render_entity_list(model.list_entities(), property_list)
    new_button = create_action.render(model)
    breadcrumbs = create_breadcrumbs(model.parent())
    return render_view(title, breadcrumbs, entity_table, buttons=[new_button])

class ListView(View):
    methods = ['GET', 'POST']
    
    def __init__(self, name, create_action):
        self.name = name
        self.create_action = create_action
        
    def render_entities(self, parent, form):
        entity_list = self.load_entities(parent)
        fields = self.get_fields(form)
        return render_entity_list(entity_list, fields)

    def dispatch_request(self, db_id=None):
        parent = data_models.lookup_entity(db_id)
        entity = self.create_entity(parent)
        form = self.create_form(request.form, entity)
        committee = data_models.get_owning_committee(parent)
        model = data_models.Model(committee)
        model.add_form('create', form)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            self.create_action.apply_to(entity, model.user)
            self.create_action.audit(entity, model.user)
            return redirect(request.base_url)
        
        entity_table = self.render_entities(parent, form)
        breadcrumbs = create_breadcrumbs(parent)
        buttons = view_actions([self.create_action], model, None)
        return render_view(self.name + ' List', breadcrumbs, entity_table, buttons=buttons)

def render_view(title, breadcrumbs, content, links=[], buttons=""):
    breadcrumbHtml = renderers.render_div(*breadcrumbs);
    nav = renderers.render_nav(*links)
    main = renderers.render_div(nav, buttons, content)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbHtml, user=render_user(), main=main)

def process_action_button(action, model, entity):
    if (request.method == 'POST' and request.form.has_key('_action')
             and request.form['_action'] == action.name):
        if not action.is_allowed(model, entity):
            raise Exception("Illegal action %s was performed" % action.name)
        return True

    return False
    
def view_actions(action_list, model, entity):
    buttons = [action.render(model, entity) for action in action_list]
    return renderers.render_nav(*buttons)

def process_edit_button(action, form, entity):
    if request.method == 'POST' and request.form.get('_action') == 'update' and form.validate():
        form.populate_obj(entity)
        entity.put()
        action.audit(entity, user)
        return True
    return False

def view_std_entity(model, title, property_list, action_list):
    if request.method == 'POST'and handle_post(model, action_list):
        return redirect(request.base_url)
    buttons = [action.render(model) for action in action_list]
    breadcrumbs = create_breadcrumbs_list(model.entity)
    content = render_entity(model.entity, property_list, 1)
    history = render_entity_history(model.entity.key)
    return render_view(title, breadcrumbs, [content, history], buttons=buttons)

class EntityView(View):
    methods = ['GET', 'POST', 'DELETE']

    def __init__(self, update_action, num_wide=0, *actions):
        self.update_action = update_action
        self.num_wide = num_wide
        self.actions = actions

    def get_links(self, entity):
        return []
        
    def dispatch_request(self, db_id):
        entity = data_models.lookup_entity(db_id)
        form = self.create_form(request.form, entity)
        committee = data_models.get_owning_committee(entity)
        model = data_models.Model(committee)
        model.add_form('update', form)
        if process_edit_button(self.update_action, form, entity):
            return redirect(request.base_url)    
        for action in self.actions:
          if process_action_button(action, model, entity):
            action.apply_to(entity, model.user)
            action.audit(entity, model.user)
            return redirect(request.base_url)
        title = self.title(entity)
        breadcrumbs = create_breadcrumbs_list(entity)
        links = self.get_links(entity)
        fields = self.get_fields(form)
        grid = render_entity(entity, fields, self.num_wide)
        history = render_entity_history(entity.key)
        buttons = view_actions([self.update_action] + list(self.actions), model, entity)
        return render_view(title, breadcrumbs, (grid, history), links, buttons)
