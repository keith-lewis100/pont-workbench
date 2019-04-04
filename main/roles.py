#_*_ coding: UTF-8 _*_

import wtforms

import db
import data_models
import custom_fields
import properties
import views
from role_types import RoleType, get_choices

ACTION_UPDATE = views.update_action(RoleType.USER_ADMIN)
ACTION_CREATE = views.create_action(RoleType.USER_ADMIN)

class RoleForm(wtforms.Form):
    type_index = custom_fields.SelectField(label='Role Type', coerce=int, choices=get_choices())
    committee = custom_fields.SelectField(choices=[("", "")] + data_models.committee_labels)
    
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
        return map(properties.create_readonly_field, form._fields.keys(), form._fields.values())

class RoleView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE)

    def title(self, entity):
        return 'Role'
                
    def create_form(self, request_input, entity):
        return RoleForm(request_input, obj=entity)
        
    def get_fields(self, form):
        return map(properties.create_readonly_field, form._fields.keys(), form._fields.values())

def add_rules(app):
    app.add_url_rule('/role_list/<db_id>', view_func=RoleListView.as_view('view_role_list'))
    app.add_url_rule('/role/<db_id>/', view_func=RoleView.as_view('view_role'))        
