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
import states
from role_types import RoleType

PROJECT_APPROVAL_PENDING = states.State('Approval Pending', True, {'approve': RoleType.PROJECT_APPROVER}) # 1
PROJECT_APPROVED = states.State('Approved', True) # 2
PROJECT_CLOSED = states.State('Closed') # 0
state_map = {
    'approve': 2,
    'cancel': 0
}

projectStates = [PROJECT_CLOSED, PROJECT_APPROVAL_PENDING, PROJECT_APPROVED]

class ProjectForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()
    committee = custom_fields.SelectField(label='Primary Committee', choices=model.committee_labels)
    multi_committee = wtforms.BooleanField()
    
class ProjectModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Project', RoleType.PROJECT_CREATOR, None, projectStates)

    def create_entity(self, parent):
        return db.Project(parent=parent.key)

    def load_entities(self, parent):
        return db.Project.query(ancestor=parent.key).fetch()
        
    def title(self, entity):
        return 'Project ' + entity.name
    
    def perform_state_change(self, entity, action):
        entity.state_index = state_map.get(action)

project_model = ProjectModel()
        
class ProjectListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, project_model, ProjectForm)
        
    def get_fields(self, form):
        state = views.StateField(projectStates)
        return (form._fields['name'], state)

class ProjectView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, project_model, ProjectForm, ('approve', 'Approve'))
        
    def get_fields(self, form):
        state = views.StateField(projectStates)
        return form._fields.values() + [state]

def add_rules(app):
    app.add_url_rule('/project_list/<db_id>', view_func=ProjectListView.as_view('view_project_list'))
    app.add_url_rule('/project/<db_id>/', view_func=ProjectView.as_view('view_project'))
    app.add_url_rule('/project/<db_id>/menu', view_func=views.MenuView.as_view('handle_project_menu', project_model))
