#_*_ coding: UTF-8 _*_

from flask import request, redirect, render_template
import wtforms
import wtforms.widgets.html5 as widgets
from datetime import date, timedelta

from application import app
import db
import data_models
import views
import custom_fields
import properties
from role_types import RoleType

STATE_WAITING = 1
STATE_READY = 2
STATE_TRANSFERED = 3 # derived state
STATE_CLOSED = 0

state_labels = ['Closed', 'Waiting', 'Ready', 'Transferred']

def state_of(grant):
    state = grant.state_index
    if state == STATE_READY and grant.transfer:
        transfer = grant.transfer.get()
        if transfer.exchange_rate:
            return STATE_TRANSFERED
    return state

class GrantModel(data_models.Model):
    def get_state(self):
        return state_of(self.entity)

def perform_create(model, action_name):
    form = model.get_form(action_name)
    if not form.validate():
        return False
    entity = model.entity
    form.populate_obj(entity)
    entity.creator = model.user.key
    supplier_fund = entity.project.parent()
    entity.supplier = supplier_fund.parent()
    entity.transfer = None
    entity.put()
    model.audit(action_name, "Create performed")
    return True

def perform_checked(model, action_name):
    entity = model.entity
    entity.state_index = STATE_READY
    entity.transfer = None
    entity.put()
    model.audit(action_name, 'Checked performed')

ACTION_CHECKED = views.StateAction('checked', 'Funds Checked', RoleType.FUND_ADMIN,
                                   perform_checked, [STATE_WAITING])
ACTION_ACKNOWLEDGED = views.StateAction('ack', 'Received', RoleType.COMMITTEE_ADMIN,
                                        data_models.Model.perform_close, [STATE_TRANSFERED])
ACTION_CANCEL = views.cancel_action(RoleType.COMMITTEE_ADMIN, [STATE_WAITING, STATE_READY])
ACTION_UPDATE = views.update_action(RoleType.COMMITTEE_ADMIN, [STATE_WAITING])
ACTION_CREATE = views.Action('create', 'New', RoleType.COMMITTEE_ADMIN, perform_create)

action_list = [ACTION_UPDATE, ACTION_CHECKED, ACTION_ACKNOWLEDGED, ACTION_CANCEL]

state_field = properties.SelectProperty(state_of, 'State', enumerate(state_labels))
creator_field = properties.KeyProperty('creator', 'Requestor')
project_field = properties.KeyProperty('project')
amount_field = properties.StringProperty('amount')
transferred_amount_field = properties.StringProperty(data_models.calculate_transferred_amount, 'Transferred Amount')
source_field = properties.StringProperty(lambda e: e.key.parent().get().code, 'Source Fund')
target_date_field = properties.DateProperty('target_date', format='%Y-%m')
description_field = properties.StringProperty('description')
foreign_transfer_field = properties.KeyProperty('transfer', title_of=lambda e: e.ref_id)

class GrantForm(wtforms.Form):
    amount = wtforms.FormField(custom_fields.MoneyForm, label='Requested Amount', widget=custom_fields.form_field_widget)
    project = custom_fields.SelectField(coerce=data_models.create_key, validators=[wtforms.validators.InputRequired()])
    target_date = wtforms.DateField(widget=widgets.MonthInput(), format='%Y-%m',
                                validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

def add_grant_form(request_input, model, action):
    form = GrantForm(request_input, obj=model.entity)
    project_list = db.Project.query(db.Project.committee == model.committee).fetch()
    custom_fields.set_field_choices(form._fields['project'], project_list)
    model.add_form(action.name, form)
       
@app.route('/grant_list/<db_id>', methods=['GET', 'POST'])
def view_grant_list(db_id):
    fund = data_models.lookup_entity(db_id)
    new_grant = db.Grant(parent=fund.key)
    new_grant.target_date = date.today() + timedelta(30)
    model = GrantModel(new_grant, fund.committee)
    add_grant_form(request.form, model, ACTION_CREATE)
    property_list = (target_date_field, project_field, amount_field, state_field)
    purchase_list = db.Grant.query(ancestor=fund.key).order(db.Grant.target_date).fetch()
    return views.view_std_entity_list(model, 'Grant List', ACTION_CREATE, property_list,
                                      purchase_list, parent=fund)

@app.route('/grant/<db_id>', methods=['GET', 'POST'])
def view_grant(db_id):
    grant = data_models.lookup_entity(db_id)
    fund = data_models.get_parent(grant)
    model = GrantModel(grant, fund.committee)
    add_grant_form(request.form, model, ACTION_UPDATE)
    title = 'Grant on ' + str(grant.target_date)
    property_list = (state_field, creator_field, transferred_amount_field, amount_field, 
                     project_field, target_date_field, foreign_transfer_field, description_field)
    return views.view_std_entity(model, title, property_list, action_list)
