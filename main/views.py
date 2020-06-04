#_*_ coding: UTF-8 _*_

from flask import render_template, redirect, request
from flask.views import View

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
    listBreadcrumbs = create_breadcrumbs_list(entity)
    return listBreadcrumbs + [" / ", renderers.render_link(entity.name, urls.url_for_entity(entity))]

def create_breadcrumbs_list(entity):
    parent = data_models.get_parent(entity)
    breadcrumbs = create_breadcrumbs(parent)
    kind = entity.key.kind()
    query_parameters = {}
    if hasattr(entity, 'state_index') and entity.state_index == 0:
        query_parameters = { 'show_closed': 'y' }
    url = urls.url_for_list(kind, parent, **query_parameters)
    return breadcrumbs + [" / ", renderers.render_link(kind + " List", url)]

def view_breadcrumbs(entity):
    breadcrumbs = create_breadcrumbs(entity)
    return renderers.render_div(*breadcrumbs)

def view_breadcrumbs_list(entity):
    breadcrumbs = create_breadcrumbs_list(entity)
    return renderers.render_div(*breadcrumbs)

def view_entity(entity, fields, num_wide=0):
    values = properties.display_entity(entity, fields)
    labels = properties.get_labels(fields)
    return renderers.render_grid(values, labels, num_wide)

def view_entity_single_column(entity, fields):
    values = properties.display_entity(entity, fields)
    labels = properties.get_labels(fields)
    return renderers.render_single_column(values, labels)    

def view_entity_list(entity_list, fields, selectable=True, no_links=True):
    column_headers = properties.get_labels(fields)
    grid = properties.display_entity_list(entity_list, fields, no_links)
    url_list = map(urls.url_for_entity, entity_list) if selectable else None
    return renderers.render_table(column_headers, grid, url_list)

def view_link(kind, label, parent=None):
    url = urls.url_for_list(kind, parent)
    return renderers.render_link(label, url, class_="button")

def view_links(parent, *link_pairs):
    links = [view_link(kind, label, parent) for kind, label in link_pairs]
    return renderers.render_nav(*links)

def view_errors(model):
    return renderers.render_errors(model.errors)

audit_fields = [
    properties.DateProperty('timestamp'),
    properties.StringProperty('message'),
    properties.KeyProperty('user')
]

def view_entity_history(key):
    audit_list = db.AuditRecord.query(db.AuditRecord.entity == key).order(-db.AuditRecord.timestamp
                      ).iter(limit = 20)
    sub_heading = renderers.sub_heading('Activity Log')
    table = view_entity_list(audit_list, audit_fields, selectable=False, no_links=False)
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
        if not enabled:
            model.add_error("Cannot perform requested action %s" % self.name)
            return False
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

class FilterAction:
    def render(self, model):
        label = 'Show Open' if model.show_closed else 'Show Closed'
        query_params = {} if model.show_closed else { 'show_closed': 'y' }
        parent = data_models.get_parent(model.entity)
        url = urls.url_for_list(model.entity.key.kind(), parent, **query_params)
        return renderers.render_link(label, url, class_='button')
    
ACTION_FILTER = FilterAction()

def update_action(required_role, allowed_states=None):
    if allowed_states is None:
        return Action('update', 'Edit', required_role, data_models.Model.perform_update)
    return StateAction('update', 'Edit', required_role, data_models.Model.perform_update, allowed_states)

def create_action(required_role):
    return Action('create', 'New', required_role, data_models.Model.perform_create)

def cancel_action(required_role, allowed_states):
    return StateAction('cancel', 'Cancel', required_role,
                       data_models.Model.perform_close, allowed_states)

def requested_action(action_list):
    action_name = request.form['_action']
    for action in action_list:
        if action.name == action_name:
            return action
    raise NotImplemented        

def handle_post(model, action_list):
    action = requested_action(action_list)
    return action.process_input(model)

def view_std_entity_list(model, title, create_action, property_list, entity_query, parent=None):
    if request.method == 'POST' and create_action.process_input(model):
        return redirect(request.base_url)
    action_list = [create_action]
    if model.is_stateful():
        model.show_closed = request.args.has_key('show_closed')
        action_list.append(ACTION_FILTER)
    entity_table = view_entity_list(model.apply_query(entity_query), property_list)
    buttons = view_actions(action_list, model)
    errors = view_errors(model)
    breadcrumbs = view_breadcrumbs(parent)
    user_controls = view_user_controls(model)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbs, user=user_controls,
                           buttons=buttons, errors=errors, content=entity_table)

def view_actions(action_list, model):
    buttons = [action.render(model) for action in action_list]
    return renderers.render_nav(*buttons)

def redirect_url(model):
    if model.entity_deleted:
        kind = model.entity.key.kind()
        parent = data_models.get_parent(model.entity)
        return urls.url_for_list(kind, parent)
    return request.base_url

def view_std_entity(model, title, property_list, action_list=[], num_wide=0, link_pairs=[]):
    if request.method == 'POST'and handle_post(model, action_list):
        return redirect(redirect_url(model))
    entity = model.entity
    links = view_links(entity, *link_pairs)
    buttons = view_actions(action_list, model)
    errors = view_errors(model)
    breadcrumbs = view_breadcrumbs_list(entity)
    grid = view_entity(entity, property_list, num_wide)
    history = view_entity_history(entity.key)
    content = renderers.render_div(grid, history)
    user_controls = view_user_controls(model)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbs, user=user_controls,
                           links=links, buttons=buttons, errors=errors, content=content)
