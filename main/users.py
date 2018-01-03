#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import model
import views
import renderers
import custom_fields

class UserForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    email =  wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class UserListView(views.ListView):
    def __init__(self):
        self.kind = 'User'
        self.formClass = UserForm
        
    def create_entity(self, parent):
        return model.create_user()

    def load_entities(self, parent):
        return model.list_users()
        
    def get_fields(self, form):
        return form._fields.values()

class UserView(views.EntityView):
    def __init__(self):
        self.formClass = UserForm
        self.actions = []
        
    def get_fields(self, form):
        return form._fields.values()
        
    def title(self, entity):
        return "User " + entity.name

    def get_links(self, entity):
        roles_url = url_for('view_role_list', db_id=entity.key.urlsafe())
        showRoles = renderers.render_link('Show Roles', roles_url, class_="button")        
        return renderers.render_nav(showRoles)

def add_rules(app):
    app.add_url_rule('/user_list', view_func=UserListView.as_view('view_user_list'))
    app.add_url_rule('/user/<db_id>/', view_func=UserView.as_view('view_user'))
