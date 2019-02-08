#_*_ coding: UTF-8 _*_

from flask import redirect, request, url_for
import wtforms

import db
import model
import custom_fields
import views
import logging
import role_types

class RoleForm(wtforms.Form):
    type_index = wtforms.SelectField(label='Role Type', coerce=int, choices=role_types.get_choices())
    committee = wtforms.SelectField(choices=[("", "")] + model.committee_labels)
    
class RoleModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Role', role_types.RoleType.USER_ADMIN)

    def create_entity(self, parent):
        return db.Role(parent=parent.key)

    def load_entities(self, parent):
        return db.Role.query(ancestor=parent.key).fetch()

    def title(self, entity):
        return 'Role'

role_model = RoleModel()

class RoleListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, role_model)
                
    def create_form(self, request_input, entity):
        return RoleForm(request_input, obj=entity)

    def get_fields(self, form):
        return map(views.create_form_field, form._fields.keys(), form._fields.values())

class RoleView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, role_model)
                
    def create_form(self, request_input, entity):
        return RoleForm(request_input, obj=entity)
        
    def get_fields(self, form):
        return map(views.create_form_field, form._fields.keys(), form._fields.values())
    
    def get_links(self, entity):
         return []

def add_rules(app):
    app.add_url_rule('/role_list/<db_id>', view_func=RoleListView.as_view('view_role_list'))
    app.add_url_rule('/role/<db_id>/', view_func=RoleView.as_view('view_role'))        
