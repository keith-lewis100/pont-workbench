#_*_ coding: UTF-8 _*_

from application import app
from flask import request
import wtforms

import db
import data_models
import renderers
import custom_fields
import properties
import views
from role_types import RoleType

TRANSFER_PENDING = 1
TRANSFER_COMPLETE = 0

state_labels = ['Closed', 'Pending']

state_field = properties.SelectProperty('state_index', 'State', enumerate(state_labels))
description_field = properties.StringProperty('description')

def perform_transferred(model, action_name):
    model.entity.state_index = TRANSFER_COMPLETE
    model.entity.put()
    model.audit(action_name, "Transfer performed")
    return True

ACTION_TRANSFERRED = views.StateAction('transferred', 'Transferred', RoleType.FUND_ADMIN,
                            perform_transferred, [TRANSFER_PENDING])
ACTION_UPDATE = views.update_action(RoleType.COMMITTEE_ADMIN, [TRANSFER_PENDING])
ACTION_CREATE = views.create_action(RoleType.COMMITTEE_ADMIN)
ACTION_CANCEL = views.cancel_action(RoleType.COMMITTEE_ADMIN, [TRANSFER_PENDING])
action_list = [ACTION_UPDATE, ACTION_TRANSFERRED, ACTION_CANCEL]

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class InternalTransferForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=custom_fields.form_field_widget)
    dest_fund = custom_fields.SelectField('Destination Fund', coerce=data_models.create_key, 
                    validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

def add_transfer_form(request_data, model, action):
    form = InternalTransferForm(request_data, obj=model.entity)
    fund_list = db.Fund.query().order(db.Fund.name).fetch()
    custom_fields.set_field_choices(form.dest_fund, fund_list)
    model.add_form(action.name, form)

@app.route('/internaltransfer_list/<db_id>', methods=['GET', 'POST'])
def view_internaltransfer_list(db_id):
    fund = data_models.lookup_entity(db_id)
    new_transfer = db.InternalTransfer(parent=fund.key)
    model = data_models.Model(new_transfer, fund.committee, db.InternalTransfer)
    add_transfer_form(request.form, model, ACTION_CREATE)   
    property_list = (state_field, properties.KeyProperty('dest_fund'),
              properties.StringProperty('amount'))
    transfer_query = db.InternalTransfer.query(ancestor = fund.key).order(-db.InternalTransfer.state_index)
    return views.view_std_entity_list(model, 'Internal Transfer List', ACTION_CREATE, property_list, 
                                      transfer_query, fund, description_field)

@app.route('/internaltransfer/<db_id>', methods=['GET', 'POST'])
def view_internaltransfer(db_id):
    transfer = data_models.lookup_entity(db_id)
    fund = data_models.get_parent(transfer)
    model = data_models.Model(transfer, fund.committee)
    add_transfer_form(request.form, model, ACTION_UPDATE)
    title = 'InternalTransfer to ' + transfer.dest_fund.get().name if transfer.dest_fund != None else ""
    property_list = (state_field, properties.KeyProperty('creator'), properties.KeyProperty('dest_fund'),
              properties.StringProperty('amount'), description_field)
    return views.view_std_entity(model, title, property_list, action_list)
