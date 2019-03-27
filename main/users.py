#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import db
import data_models
import views
import renderers
import custom_fields
import properties
from role_types import RoleType

ACTION_UPDATE = views.update_action(RoleType.USER_ADMIN)
ACTION_CREATE = views.create_action(RoleType.USER_ADMIN)

class UserForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    email =  wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    
class UserListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'User', ACTION_CREATE)

    def load_entities(self, parent):
        return db.User.query().fetch()
        
    def create_entity(self, parent):
        return db.User()
        
    def create_form(self, request_input, entity):
        return UserForm(request_input, obj=entity)

    def get_fields(self, form):
        return map(properties.create_readonly_field, form._fields.keys(), form._fields.values())

class UserView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE)

    def title(self, entity):
        return 'User ' + entity.name
        
    def create_form(self, request_input, entity):
        return UserForm(request_input, obj=entity)
        
    def get_fields(self, form):
        return map(properties.create_readonly_field, form._fields.keys(), form._fields.values())
        
    def get_links(self, entity):
        return (views.render_link('Role', 'Show Roles', entity), )

def add_rules(app):
    app.add_url_rule('/user_list', view_func=UserListView.as_view('view_user_list'))
    app.add_url_rule('/user/<db_id>/', view_func=UserView.as_view('view_user'))
