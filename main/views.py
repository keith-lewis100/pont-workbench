#_*_ coding: UTF-8 _*_

from flask import render_template, redirect, request
from flask.views import View
from google.appengine.api import users

import db
import renderers
import data_models
import custom_fields
import properties
import urls

def view_user_controls(model):
    logout_url = data_models.logout_url()
    return renderers.render_logout(model.user.name, logout_url)

def create_breadcrumbs(entity):
    if entity is None:
        return [renderers.render_link('Dashboard', '/')]
    parent = data_models.get_parent(entity)
    listBreadcrumbs = create_breadcrumbs_list(parent, entity.key.kind())
    return listBreadcrumbs + [" / ", renderers.render_link(entity.name, urls.url_for_entity(entity))]

def create_breadcrumbs_list(parent, kind):
    breadcrumbs = create_breadcrumbs(parent)
    return breadcrumbs + [" / ", renderers.render_link(kind + " List", urls.url_for_list(kind, parent))]

def view_breadcrumbs(entity, list_kind=None):
    if list_kind:
        breadcrumbs = create_breadcrumbs_list(entity, list_kind)
    else:
        breadcrumbs = create_breadcrumbs(entity)
    return renderers.render_div(*breadcrumbs)

def render_entity(entity, fields, num_wide=0):
    values = properties.display_entity(entity, fields)
    labels = properties.get_labels(fields)
    return renderers.render_grid(values, labels, num_wide)

def render_entity_list(entity_list, fields, selectable=True):
    column_headers = properties.get_labels(fields)
    grid = properties.display_entity_list(entity_list, fields, selectable)
    url_list = map(urls.url_for_entity, entity_list) if selectable else None
    return renderers.render_table(column_headers, grid, url_list)

def render_link(kind, label, parent=None):
    url = urls.url_for_list(kind, parent)
    return renderers.render_link(label, url, class_="button")

def view_links(parent, *link_pairs):
    links = [render_link(lind, label, parent) for kind, label in link_pairs]
    return renderers.nav(*links)

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
    def __init__(self, name, label, required_role, perform):
        self.name = name
        self.label = label
        self.required_role = required_role
        self.perform = perform

    def is_allowed(self, model):
        return model.user_has_role(self.required_role)

    def process_input(self, model):
        enabled = self.is_allowed(model)
        assert enabled
        return self.perform(model, self.name)

    def render(self, model):
        enabled = self.is_allowed(model)
        form = model.get_form(self.name)
        if form:
            return custom_fields.render_dialog_button(self.label, self.name, form, enabled)
        return renderers.render_submit_button(self.label, name='_action', value=self.name,
                disabled=not enabled)

class StateAction(Action):
    def __init__(self, name, label, required_role, perform, allowed_states):
        super(StateAction, self).__init__(name, label, required_role, perform)
        self.allowed_states = allowed_states

    def is_allowed(self, model):
        if not super(StateAction, self).is_allowed(model):
            return False
        state = model.get_state()
        return state in self.allowed_states

def update_action(required_role, allowed_states=None):
    if allowed_states is None:
        return Action('update', 'Edit', required_role, data_models.Model.perform_update)
    return StateAction('update', 'Edit', required_role, data_models.Model.perform_update, allowed_states)

def create_action(required_role):
    return Action('create', 'New', required_role, data_models.Model.perform_create)

def handle_post(model, action_list):
    action_name = request.form['_action']
    for action in action_list:
        if action.name == action_name:
            return action.process_input(model)
    raise NotImplemented        

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
        model = data_models.Model(entity, committee)
        model.add_form('create', form)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            self.create_action.apply_to(entity, model.user)
            self.create_action.audit(entity, model.user)
            return redirect(request.base_url)
        entity_table = self.render_entities(parent, form)
        breadcrumbs = view_breadcrumbs(parent)
        buttons = view_actions([self.create_action], model, None)
        user_controls = view_user_controls(model)
        return render_view(self.name + ' List', user_controls, breadcrumbs, entity_table, buttons=buttons)

def render_view(title, user_controls, breadcrumbs, content_list, links="", buttons=""):
    content = renderers.render_div(content_list)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbs, user=user_controls,
                           links=links, buttons=buttons, content=content)

def process_action_button(action, model):
    if (request.method == 'POST' and request.form.has_key('_action')
             and request.form['_action'] == action.name):
        if not action.is_allowed(model):
            raise Exception("Illegal action %s was performed" % action.name)
        return True

    return False
    
def view_actions(action_list, model):
    buttons = [action.render(model) for action in action_list]
    return renderers.render_nav(*buttons)

def process_edit_button(action, form, entity):
    if request.method == 'POST' and request.form.get('_action') == 'update' and form.validate():
        form.populate_obj(entity)
        entity.put()
        action.audit(entity, user)
        return True
    return False

def view_std_entity(model, title, property_list, action_list=[], num_wide=0, links=[]):
    if request.method == 'POST'and handle_post(model, action_list):
        return redirect(request.base_url)
    buttons = [action.render(model) for action in action_list]
    parent = data_models.get_parent(model.entity)
    breadcrumbs = view_breadcrumbs(parent, model.entity.key.kind())
    grid = render_entity(model.entity, property_list, num_wide)
    history = render_entity_history(model.entity.key)
    content = renderers.render_div(grid, history)
    user_controls = view_user_controls(model)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbs, user=user_controls,
                           links=links, buttons=buttons, content=content)
class EntityView(View):
    methods = ['GET', 'POST']

    def __init__(self, update_action, num_wide=0, *actions):
        self.update_action = update_action
        self.num_wide = num_wide
        self.actions = actions

    def get_link_pairs(self):
        return []
        
    def dispatch_request(self, db_id):
        entity = data_models.lookup_entity(db_id)
        form = self.create_form(request.form, entity)
        committee = data_models.get_owning_committee(entity)
        model = data_models.Model(entity, committee)
        model.add_form('update', form)
        if process_edit_button(self.update_action, form, entity):
            return redirect(request.base_url)    
        for action in self.actions:
          if process_action_button(action, model):
            action.apply_to(entity, model.user)
            action.audit(entity, model.user)
            return redirect(request.base_url)
        title = self.title(entity)
        parent = data_models.get_parent(entity)
        breadcrumbs = view_breadcrumbs(parent, entity.key.kind())
        links = view_links(entity, *self.get_link_pairs())
        fields = self.get_fields(form)
        grid = render_entity(entity, fields, self.num_wide)
        history = render_entity_history(entity.key)
        buttons = view_actions([self.update_action] + list(self.actions), model, entity)
        content = renderers.render_div(grid, history)
        user_controls = view_user_controls(model)
        return render_template('layout.html', title=title, breadcrumbs=breadcrumbs, user=user_controls,
                           links=links, buttons=buttons, content=content)
