#_*_ coding: UTF-8 _*_

from flask import request, redirect, url_for
import wtforms

from application import app
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
def state_of(entity):
    return state_labels[entity.state_index]

state_field = properties.StringProperty(state_of, 'State')

class InternalTransferModel(data_models.Model):
    pass

ACTION_TRANSFERRED = views.StateAction('transferred', 'Transferred', RoleType.FUND_ADMIN, 
                            [TRANSFER_PENDING])
ACTION_UPDATE = views.update_action(RoleType.COMMITTEE_ADMIN, [TRANSFER_PENDING])
ACTION_CREATE = views.create_action(RoleType.COMMITTEE_ADMIN)
action_list = [ACTION_UPDATE, ACTION_TRANSFERRED]

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class InternalTransferForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=custom_fields.form_field_widget)
    dest_fund = custom_fields.SelectField('Destination Fund', coerce=data_models.create_key, 
                    validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

def add_transfer_form(request_data, model, action):
    form = InternalTransferForm(request_data, obj=model.entity)
    fund_list = db.Fund.query().fetch()
    custom_fields.set_field_choices(form.dest_fund, fund_list)
    model.add_form(action.name, form)

@app.route('/internaltransfer_list/<db_id>', methods=['GET', 'POST'])
def view_internaltransfer_list(db_id):
    fund = data_models.lookup_entity(db_id, 'Fund')
    new_transfer = db.InternalTransfer(parent=fund.key)
    model = InternalTransferModel(new_transfer, db.InternalTransfer)
    add_transfer_form(request.form, model, ACTION_CREATE)   
    property_list = (properties.KeyProperty('dest_fund'),
              properties.StringProperty('amount'), state_field)
    return views.view_entity_list(model, 'Internal Transfer List', property_list, ACTION_CREATE)

@app.route('/internaltransfer/<db_id>', methods=['GET', 'POST'])
def view_internaltransfer(db_id):
    transfer = data_models.lookup_entity(db_id, 'InternalTransfer')
    model = InternalTransferModel(transfer)
    add_transfer_form(request.form, model, ACTION_UPDATE)
    title = 'InternalTransfer to ' + transfer.dest_fund.get().name if transfer.dest_fund != None else ""
    property_list = (state_field, properties.KeyProperty('creator'), properties.KeyProperty('dest_fund'),
              properties.StringProperty('amount'), properties.StringProperty('description'))
    return views.view_std_entity(model, title, property_list, action_list)
