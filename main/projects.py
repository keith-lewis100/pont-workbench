#_*_ coding: UTF-8 _*_

import wtforms

import db
import data_models
import custom_fields
import properties
import views
from role_types import RoleType

STATE_APPROVAL_PENDING = 1
STATE_APPROVED = 2
STATE_CLOSED = 0

state_names = ['Closed', 'Pending', 'Approved']

state_field = properties.SelectProperty('state_index', 'State', enumerate(state_names))

def perform_approve(model, action_name):
    model.entity.state_index = STATE_APPROVED
    model.entity.put()
    model.audit(action_name, 'Approved performed')
    return True

ACTION_APPROVE = views.StateAction('approve', 'Approve', RoleType.PROJECT_APPROVER,
                                   perform_approve, [STATE_APPROVAL_PENDING])
ACTION_UPDATE = views.update_action(RoleType.PROJECT_CREATOR, [STATE_APPROVAL_PENDING, STATE_APPROVED])
ACTION_CREATE = views.create_action(RoleType.PROJECT_CREATOR)

class ProjectForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    committee = custom_fields.SelectField(label='Primary Committee', choices=data_models.committee_labels)
    multi_committee = wtforms.BooleanField()
    partner = custom_fields.SelectField(coerce=data_models.create_key, validators=[wtforms.validators.Optional()])
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
        return (properties.StringProperty('name', 'Name'), state_field)

class ProjectView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE, 1, ACTION_APPROVE)
        
    def title(self, entity):
        return 'Project ' + entity.name
        
    def create_form(self, request_input, entity):
        return create_project_form(request_input, entity)
        
    def get_fields(self, form):
        return [state_field] + map(properties.create_readonly_field, 
                   form._fields.keys(), form._fields.values())

def add_rules(app):
    app.add_url_rule('/project_list/<db_id>', view_func=ProjectListView.as_view('view_project_list'))
    app.add_url_rule('/project/<db_id>/', view_func=ProjectView.as_view('view_project'))
