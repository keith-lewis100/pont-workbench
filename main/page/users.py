#_*_ coding: UTF-8 _*_

from flask import request
from application import app
import wtforms

import custom_fields
import data_models
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

@app.route('/user_list', methods=['GET', 'POST'])
def view_user_list():
    new_user = db.User()
    model = data_models.Model(new_user, None, db.User)
    form = UserForm(request.form, obj=new_user)
    model.add_form(ACTION_CREATE.name, form)
    user_query = db.User.query().order(db.User.name)
    property_list = (name_field, email_field)
    return views.view_std_entity_list(model, 'User List', ACTION_CREATE, property_list,
                                      user_query)

link_pairs = [('Role', 'Show Roles')]

@app.route('/user/<db_id>', methods=['GET', 'POST'])
def view_user(db_id):
    user = data_models.lookup_entity(db_id)
    model = data_models.Model(user, None, db.User)
    form = UserForm(request.form, obj=user)
    model.add_form(ACTION_UPDATE.name, form)
    property_list = (name_field, email_field)
    return views.view_std_entity(model, 'User ' + user.name, property_list, (ACTION_UPDATE, ),
                                 0, link_pairs)    
