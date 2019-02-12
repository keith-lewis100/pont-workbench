#_*_ coding: UTF-8 _*_

from flask import url_for, render_template
from application import app
from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import readonly_fields
import views
from role_types import RoleType

import paymentsdue

TRANSFER_CLOSED = 0
TRANSFER_REQUESTED = 1
TRANSFER_TRANSFERRED = 2

ACTION_COMPLETED = model.Action('transferred', 'Transferred', RoleType.FUND_ADMIN, TRANSFER_REQUESTED)

ref_field = readonly_fields.ReadOnlyField('ref_id')
state_field = readonly_fields.StateField('Closed', 'Requested', 'Transferred')
creator_field = readonly_fields.ReadOnlyKeyField('creator')
rate_field = readonly_fields.ReadOnlyField('exchange_rate')

class ExchangeRateForm(wtforms.Form):
    action = wtforms.HiddenField(default='transferred')
    exchange_rate = wtforms.IntegerField('Exchange Rate', validators=[wtforms.validators.InputRequired()])
        
@app.route('/foreigntransfer_list/<db_id>')
def view_foreigntransfer_list(db_id):
    supplier = model.lookup_entity(db_id)
    breadcrumbs = views.create_breadcrumbs(supplier)
    transfer_list = db.ForeignTransfer.query(ancestor=supplier.key).fetch()
    transfer_fields = [ref_field, state_field, rate_field]
    entity_table = renderers.render_table(transfer_list, views.url_for_entity, *transfer_fields)
    return views.render_view('Payments Due List', breadcrumbs, entity_table)

def process_action_button(action, entity, user, buttons, dialogs):
    if action.name != 'transferred':
        return views.EntityView.process_action_button(self, action, entity, user, buttons, dialogs)
    form = ExchangeRateForm(request.form)
    if (request.method == 'POST' and request.form.get('action') == 'transferred' 
              and form.validate()):
        form.populate_obj(entity)
        entity.state_index = TRANSFER_TRANSFERRED
        entity.put()
        return True
    rendered_form = custom_fields.render_form(form)
    dialog = renderers.render_modal_dialog(rendered_form, 'd-transferred', form.errors)
    dialogs.append(dialog)
    enabled = action.is_allowed(entity, user)
    button = renderers.render_modal_open(action.label, 'd-transferred', enabled)
    buttons.append(button)
    return False

@app.route('/foreigntransfer/<db_id>')        
def view_foreigntransfer(db_id):
    transfer = model.lookup_entity(db_id)
    transfer_fields = (ref_field, state_field, rate_field, creator_field)
    grid = renderers.render_grid(transfer, transfer_fields)
    breadcrumbs = views.create_breadcrumbs_list(transfer)
    grant_list = db.Grant.query(db.Grant.state_index == 2).fetch()
    payments_list = paymentsdue.load_payments(grant_list)
    entity_table = renderers.render_table(payments_list, views.url_for_entity, *paymentsdue.payments_field_list)
    return views.render_view('Foreign Transfer', breadcrumbs, (grid, entity_table))
