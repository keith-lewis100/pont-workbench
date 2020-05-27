#_*_ coding: UTF-8 _*_

import wtforms

import custom_fields
import db
import views
import properties
from role_types import RoleType

ACTION_UPDATE = views.update_action(RoleType.USER_ADMIN)
ACTION_CREATE = views.create_action(RoleType.USER_ADMIN)

class UserForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    email =  wtforms.StringField(validators=[wtforms.validators.InputRequired()])

name_field = properties.StringProperty('name')
email_field = properties.StringProperty('email')

class UserListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'User', ACTION_CREATE)

    def get_entity_query(self, parent):
        return db.User.query().order(db.User.name)
        
    def create_entity(self, parent):
        return db.User()
        
    def create_form(self, request_input, entity):
        return UserForm(request_input, obj=entity)

    def get_fields(self, form):
        return (name_field, email_field)

class UserView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE)

    def title(self, entity):
        return 'User ' + entity.name
        
    def create_form(self, request_input, entity):
        return UserForm(request_input, obj=entity)
        
    def get_fields(self, form):
        return (name_field, email_field)
        
    def get_link_pairs(self):
        return [('Role', 'Show Roles')]

def add_rules(app):
    app.add_url_rule('/user_list', view_func=UserListView.as_view('view_user_list'))
    app.add_url_rule('/user/<db_id>/', view_func=UserView.as_view('view_user'))
