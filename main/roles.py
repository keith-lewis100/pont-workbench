#_*_ coding: UTF-8 _*_

from flask import request
import wtforms

from application import app
import db
import data_models
import custom_fields
import properties
import views
from role_types import RoleType, get_choices

def perform_delete(model, action_name):
    model.entity.key.delete()
    parent = data_models.get_parent(model.entity)
    roleName = dict(get_choices()).get(model.entity.type_index, "")
    model.audit(action_name, "Delete role %s performed" % roleName, parent)
    model.entity_deleted = True
    return True

ACTION_UPDATE = views.update_action(RoleType.USER_ADMIN)
ACTION_CREATE = views.create_action(RoleType.USER_ADMIN)
ACTION_DELETE = views.Action('delete', 'Delete', RoleType.USER_ADMIN, perform_delete)

class RoleForm(wtforms.Form):
    type_index = custom_fields.SelectField(label='Role Type', coerce=int, choices=get_choices())
    committee = custom_fields.SelectField(choices=[("", "")] + data_models.committee_labels)

@app.route('/role_list/<db_id>', methods=['GET', 'POST'])
def view_role_list(db_id):
    user = data_models.lookup_entity(db_id)
    new_role = db.Role(parent=user.key)
    model = data_models.Model(new_role)
    form = RoleForm(request.form, new_role)
    model.add_form(ACTION_CREATE.name, form)
    property_list = map(properties.create_readonly_field, form._fields.keys(),
                        form._fields.values())
    role_list = db.Role.query(ancestor=user.key).fetch()
    return views.view_std_entity_list(model, 'Role List', ACTION_CREATE,
                                      property_list, role_list, user)

@app.route('/role/<db_id>', methods=['GET', 'POST', 'DELETE'])
def view_roles(db_id):
    role = data_models.lookup_entity(db_id)
    model = data_models.Model(role, None)
    form = RoleForm(request.form, role)
    model.add_form(ACTION_UPDATE.name, form)
    property_list = map(properties.create_readonly_field, form._fields.keys(),
                        form._fields.values())
    return views.view_std_entity(model, 'Role', property_list, [ACTION_UPDATE, ACTION_DELETE])
