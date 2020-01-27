#_*_ coding: UTF-8 _*_

import wtforms
import wtforms.widgets.html5 as widgets
import logging

import db
import data_models
import custom_fields
import properties
import views
from role_types import RoleType

def migrate_project(old_project, fund_key):
    logging.info('Migrating project %s' % old_project.name)
    supplier = fund_key.parent().get()
    new_project = db.Project(parent=supplier.key)
    new_project.name = old_project.name
    new_project.description = old_project.description
    new_project.committee = old_project.committee
    new_project.state_index = old_project.state_index
    new_project.multi_committee = old_project.multi_committee
    new_project.creator = old_project.creator
    new_project.partner = old_project.partner
    new_project.fund = fund_key
    new_project.put()
    audits = db.AuditRecord.query(db.AuditRecord.entity == old_project.key)
    for audit in audits:
        audit.entity = new_project.key
        audit.put()
    grants = db.Grant.query(db.Grant.project == old_project.key)
    for grant in grants:
        grant.project = new_project.key
        grant.put()
    old_project.key.delete()
    logging.info('Migrated project %s' % new_project.name)

old_projects = db.Project.query().fetch()
for project in old_projects:
    parent_key = project.key.parent()
    if parent_key.kind() == 'SupplierFund':
        migrate_project(project, parent_key)

STATE_APPROVAL_PENDING = 1
STATE_APPROVED = 2
STATE_CLOSED = 0

state_labels = ['Closed', 'Pending', 'Approved']
state_field = properties.SelectProperty('state_index', 'State', enumerate(state_labels))

size_labels = [(0, u'Small < £1k pa'), (1, u'Medium < £5k pa'), (2, u'Large >= £5k pa')]

def perform_approve(model, action_name):
    model.entity.state_index = STATE_APPROVED
    model.entity.put()
    model.audit(action_name, 'Approved performed')
    return True

ACTION_APPROVE = views.StateAction('approve', 'Approve', RoleType.PROJECT_APPROVER,
                                   perform_approve, [STATE_APPROVAL_PENDING])
ACTION_UPDATE = views.update_action(RoleType.PROJECT_CREATOR, [STATE_APPROVAL_PENDING, STATE_APPROVED])
ACTION_CREATE = views.create_action(RoleType.PROJECT_CREATOR)
ACTION_CLOSE = views.StateAction('close', 'Close', RoleType.PROJECT_CREATOR,
                       data_models.Model.perform_close, [STATE_APPROVAL_PENDING, STATE_APPROVED])

class ProjectForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    committee = custom_fields.SelectField(label='Primary Committee', choices=data_models.committee_labels)
    multi_committee = wtforms.BooleanField()
    fund = custom_fields.SelectField(coerce=data_models.create_key)
    partner = custom_fields.SelectField(coerce=data_models.create_key)
    size = custom_fields.SelectField(label='Project Size', coerce=int, choices=size_labels)
    grant_agreement_start = wtforms.DateField(label= 'Grant Agreement start date', widget=widgets.MonthInput(),
                                              format='%Y-%m', validators=[wtforms.validators.Optional()])
    description = wtforms.TextAreaField()

    def validate_partner(form, field):
        fund_key = form._fields['fund'].data
        if fund_key is None:
            return
        fund = fund_key.get()
        if fund.partner_required and not field.data:
            raise wtforms.ValidationError('A partner must be specified with fund - %s' % fund.name)

def create_project_form(request_input, entity):
    supplier = data_models.get_parent(entity)
    if request_input:
        form = ProjectForm(request_input)
    else:
        form = ProjectForm(obj=entity)
    partner_list = db.Partner.query(ancestor=supplier.key).order(db.Partner.name).fetch()
    partner_field = form._fields['partner']
    partner_field.flags.optional = True
    custom_fields.set_field_choices(partner_field, partner_list)
    fund_list = db.SupplierFund.query(ancestor=supplier.key).order(db.SupplierFund.name).fetch()
    fund_field = form._fields['fund']
    custom_fields.set_field_choices(fund_field, fund_list)
    return form
        
class ProjectListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'Project', ACTION_CREATE)

    def load_entities(self, parent):
        return db.Project.query(ancestor=parent.key).order(db.Project.name).fetch()

    def create_entity(self, parent):
        return db.Project(parent=parent.key)
        
    def create_form(self, request_input, entity):
        return create_project_form(request_input, entity)

    def get_fields(self, form):
        return (properties.StringProperty('name', 'Name'), state_field)

class ProjectView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE, 1, ACTION_APPROVE, ACTION_CLOSE)
        
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
