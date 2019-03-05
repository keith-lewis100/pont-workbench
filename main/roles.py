#_*_ coding: UTF-8 _*_

from flask import redirect, request, url_for
import wtforms

import db
import model
import custom_fields
import readonly_fields
import views
import logging
import role_types

ACTION_UPDATE = model.Action('edit', 'Edit', role_types.RoleType.USER_ADMIN)
ACTION_CREATE = model.CreateAction(role_types.RoleType.USER_ADMIN)

class RoleForm(wtforms.Form):
    type_index = custom_fields.SelectField(label='Role Type', coerce=int, choices=role_types.get_choices())
    committee = custom_fields.SelectField(choices=[("", "")] + model.committee_labels)
    
class RoleListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'Role', ACTION_CREATE)

    def load_entities(self, parent):
        return db.Role.query(ancestor=parent.key).fetch()

    def create_entity(self, parent):
        return db.Role(parent=parent.key)
                
    def create_form(self, request_input, entity):
        return RoleForm(request_input, obj=entity)

    def get_fields(self, form):
        return map(readonly_fields.create_readonly_field, form._fields.keys(), form._fields.values())

class RoleView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE)

    def title(self, entity):
        return 'Role'
                
    def create_form(self, request_input, entity):
        return RoleForm(request_input, obj=entity)
        
    def get_fields(self, form):
        return map(readonly_fields.create_readonly_field, form._fields.keys(), form._fields.values())
    
    def get_links(self, entity):
         return []

def add_rules(app):
    app.add_url_rule('/role_list/<db_id>', view_func=RoleListView.as_view('view_role_list'))
    app.add_url_rule('/role/<db_id>/', view_func=RoleView.as_view('view_role'))        
