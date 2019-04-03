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
    def perform_transferred(self, action_name):
        self.entity.state_index = TRANSFER_COMPLETE
        self.entity.put()
        self.audit(action_name, "Transfer performed")
        return True

ACTION_TRANSFERRED = views.StateAction('transferred', 'Transferred', RoleType.FUND_ADMIN, 
                            [TRANSFER_PENDING], InternalTransferModel.perform_transferred)
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
    model = data_models.Model(new_transfer, fund.committee)
    add_transfer_form(request.form, model, ACTION_CREATE)   
    if request.method == 'POST' and ACTION_CREATE.process_input(model):
        return redirect(request.base_url)
    property_list = (properties.KeyProperty('dest_fund'),
              properties.StringProperty('amount'), state_field)
    transfer_list = db.InternalTransfer.query(ancestor = fund.key).fetch()
    entity_table = [views.render_entity_list(transfer_list, property_list)]
    new_button = ACTION_CREATE.render(model)
    breadcrumbs = views.view_breadcrumbs(fund)
    user_controls = views.view_user_controls(model)
    return views.render_view('Internal Transfer List', user_controls, breadcrumbs, entity_table, buttons=[new_button])

@app.route('/internaltransfer/<db_id>', methods=['GET', 'POST'])
def view_internaltransfer(db_id):
    transfer = data_models.lookup_entity(db_id, 'InternalTransfer')
    fund = data_models.get_parent(transfer)
    model = data_models.Model(transfer, fund.committee)
    add_transfer_form(request.form, model, ACTION_UPDATE)
    title = 'InternalTransfer to ' + transfer.dest_fund.get().name if transfer.dest_fund != None else ""
    property_list = (state_field, properties.KeyProperty('creator'), properties.KeyProperty('dest_fund'),
              properties.StringProperty('amount'), properties.StringProperty('description'))
    return views.view_std_entity(model, title, property_list, action_list)
