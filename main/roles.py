#_*_ coding: UTF-8 _*_

from flask import redirect, request, url_for
import wtforms

import model
import renderers
import custom_fields
import views
import logging
import role_types

class RoleForm(wtforms.Form):
    type_index = custom_fields.SelectField(label='Role Type', coerce=int, choices=role_types.get_choices())
    committee = custom_fields.SelectField(choices=[("", "")] + model.committee_labels)

class Role(views.EntityType):
    def __init__(self):
        self.name = 'Role'
        self.formClass = RoleForm

    def get_state(self, index):
        return None
        
    def create_entity(self, parent):
        return model.create_role(parent)

    def load_entities(self, parent):
        return model.list_roles(parent)

    def title(self, entity):
        return 'Role'

class RoleListView(views.ListView):
    def __init__(self):
        self.entityType = Role()
                
    def get_fields(self, form):
        return form._fields.values()

class RoleView(views.EntityView):
    def __init__(self):
        self.entityType = Role()
        self.actions = []
        
    def get_fields(self, form):
        return form._fields.values()
    
    def get_links(self, entity):
         return []

def add_rules(app):
    app.add_url_rule('/role_list/<db_id>', view_func=RoleListView.as_view('view_role_list'))
    app.add_url_rule('/role/<db_id>/', view_func=RoleView.as_view('view_role'))        
