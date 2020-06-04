#_*_ coding: UTF-8 _*_

from flask import request
import wtforms
import wtforms.widgets.html5 as widgets
import logging

from application import app
import db
import data_models
import custom_fields
import properties
import views
from role_types import RoleType

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
action_list = [ACTION_UPDATE, ACTION_APPROVE, ACTION_CLOSE]

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

def create_project_form(project, supplier):
    if request.form:
        form = ProjectForm(request.form)
    else:
        form = ProjectForm(obj=project)
    partner_list = db.Partner.query(ancestor=supplier.key).order(db.Partner.name).fetch()
    partner_field = form._fields['partner']
    partner_field.flags.optional = True
    custom_fields.set_field_choices(partner_field, partner_list)
    fund_list = db.SupplierFund.query(ancestor=supplier.key).order(db.SupplierFund.name).fetch()
    fund_field = form._fields['fund']
    custom_fields.set_field_choices(fund_field, fund_list)
    return form

@app.route('/project_list/<db_id>', methods=['GET', 'POST'])
def view_project_list(db_id):
    supplier = data_models.lookup_entity(db_id)
    new_project = db.Project(parent=supplier.key)
    model = data_models.Model(new_project, None, db.Project)
    form = create_project_form(new_project, supplier)
    model.add_form(ACTION_CREATE.name, form)
    property_list = (state_field, properties.StringProperty('name', 'Name'))
    project_query = db.Project.query(ancestor=supplier.key).order(-db.Project.state_index, db.Project.name)
    return views.view_std_entity_list(model, 'Project List', ACTION_CREATE, property_list,
                                       project_query, supplier)

@app.route('/project/<db_id>', methods=['GET', 'POST'])
def view_project(db_id):
    project = data_models.lookup_entity(db_id)
    supplier = data_models.get_parent(project)
    model = data_models.Model(project, None, db.Project)
    form = create_project_form(project, supplier)
    model.add_form(ACTION_UPDATE.name, form)
    property_list = [state_field] + map(properties.create_readonly_field, 
                        form._fields.keys(), form._fields.values())
    return views.view_std_entity(model, 'Project ' + project.name, property_list, action_list, num_wide=1)    
