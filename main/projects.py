#_*_ coding: UTF-8 _*_

from flask import redirect, request, url_for
from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import views
import logging
from role_types import RoleType

PROJECT_APPROVAL_PENDING = 1
#states.State('Approval Pending', True, {'approve': RoleType.PROJECT_APPROVER}) # 1
PROJECT_APPROVED = 2
#states.State('Approved', True) # 2
PROJECT_CLOSED = 0
#states.State('Closed') # 0

state_field = views.StateField('Closed', 'Approval Pending', 'Approved')

ACTION_APPROVE = model.Action("approve", "Approve", RoleType.PROJECT_APPROVER, PROJECT_APPROVED, [PROJECT_APPROVAL_PENDING])

class ProjectForm(wtforms.Form):
    description = wtforms.TextAreaField()
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    committee = custom_fields.SelectField(label='Primary Committee', choices=model.committee_labels)
    multi_committee = wtforms.BooleanField()
    partner = custom_fields.KeyPropertyField('Partner',
                    validators=[wtforms.validators.Optional()],
                    query=db.Partner.query())
    
class ProjectModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Project', RoleType.PROJECT_CREATOR, PROJECT_APPROVAL_PENDING, PROJECT_APPROVED)

    def create_entity(self, parent):
        return db.Project(parent=parent.key)

    def load_entities(self, parent):
        return db.Project.query(ancestor=parent.key).fetch()
        
    def title(self, entity):
        return 'Project ' + entity.name

project_model = ProjectModel()
        
class ProjectListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, project_model, ProjectForm)
        
    def get_fields(self, form):
        return (form._fields['name'], state_field)

class ProjectView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, project_model, ProjectForm, ACTION_APPROVE)
        
    def get_fields(self, form):
        return form._fields.values() + [state_field]

def add_rules(app):
    app.add_url_rule('/project_list/<db_id>', view_func=ProjectListView.as_view('view_project_list'))
    app.add_url_rule('/project/<db_id>/', view_func=ProjectView.as_view('view_project'))
