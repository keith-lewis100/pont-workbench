#_*_ coding: UTF-8 _*_

from flask import redirect, request, url_for
from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import readonly_fields
import views
import logging
from role_types import RoleType

PROJECT_APPROVAL_PENDING = 1
PROJECT_APPROVED = 2
PROJECT_CLOSED = 0

state_field = readonly_fields.StateField('Closed', 'Approval Pending', 'Approved')

ACTION_APPROVE = model.StateAction("approve", "Approve", RoleType.PROJECT_APPROVER, PROJECT_APPROVED, [PROJECT_APPROVAL_PENDING])
ACTION_UPDATE = model.StateAction('edit', 'Edit', RoleType.PROJECT_CREATOR, None, [PROJECT_APPROVAL_PENDING, PROJECT_APPROVED])
ACTION_CREATE = model.CreateAction(RoleType.PROJECT_CREATOR)

class ProjectForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    committee = custom_fields.SelectField(label='Primary Committee', choices=model.committee_labels)
    multi_committee = wtforms.BooleanField()
    partner = custom_fields.SelectField(coerce=model.create_key, validators=[wtforms.validators.Optional()])
    description = wtforms.TextAreaField()
    
def create_project_form(request_input, entity):
    form = ProjectForm(request_input, obj=entity)
    partner_list = db.Partner.query().fetch()
    custom_fields.set_field_choices(form._fields['partner'], partner_list)
    return form
        
class ProjectListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'Project', ACTION_CREATE)

    def load_entities(self, parent):
        return db.Project.query(ancestor=parent.key).fetch()

    def create_entity(self, parent):
        return db.Project(parent=parent.key)
        
    def create_form(self, request_input, entity):
        return create_project_form(request_input, entity)

    def get_fields(self, form):
        return (readonly_fields.ReadOnlyField('name', 'Name'), state_field)

class ProjectView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE, 1, ACTION_APPROVE)
        
    def title(self, entity):
        return 'Project ' + entity.name
        
    def create_form(self, request_input, entity):
        return create_project_form(request_input, entity)
        
    def get_fields(self, form):
        return [state_field] + map(readonly_fields.create_readonly_field, 
                   form._fields.keys(), form._fields.values())

def add_rules(app):
    app.add_url_rule('/project_list/<db_id>', view_func=ProjectListView.as_view('view_project_list'))
    app.add_url_rule('/project/<db_id>/', view_func=ProjectView.as_view('view_project'))
