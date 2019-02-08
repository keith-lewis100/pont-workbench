#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import db
import model
import views
import renderers
import custom_fields
from role_types import RoleType

class UserForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    email =  wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    
class UserModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'User', RoleType.USER_ADMIN)
        
    def create_entity(self, parent):
        return db.User()

    def load_entities(self, parent):
        return db.User.query().fetch()
        
    def title(self, entity):
        return 'User ' + entity.name

user_model = UserModel()

class UserListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, user_model)
        
    def create_form(self, request_input, entity):
        return UserForm(request_input, obj=entity)

    def get_fields(self, form):
        return map(views.create_form_field, form._fields.keys(), form._fields.values())

class UserView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, user_model)
        
    def create_form(self, request_input, entity):
        return UserForm(request_input, obj=entity)
        
    def get_fields(self, form):
        return map(views.create_form_field, form._fields.keys(), form._fields.values())
        
    def get_links(self, entity):
        roles_url = url_for('view_role_list', db_id=entity.key.urlsafe())
        showRoles = renderers.render_link('Show Roles', roles_url, class_="button")        
        return [showRoles]

def add_rules(app):
    app.add_url_rule('/user_list', view_func=UserListView.as_view('view_user_list'))
    app.add_url_rule('/user/<db_id>/', view_func=UserView.as_view('view_user'))
