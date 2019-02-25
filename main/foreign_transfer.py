#_*_ coding: UTF-8 _*_

from flask import url_for, request, redirect
from application import app
from flask.views import View
import wtforms
from datetime import date

import db
import model
import renderers
import custom_fields
import readonly_fields
import views
from role_types import RoleType

import grants
import paymentsdue

TRANSFER_CLOSED = 0
TRANSFER_REQUESTED = 1
TRANSFER_TRANSFERRED = 2

ACTION_TRANSFERRED = model.StateAction('transferred', 'Transferred', RoleType.PAYMENT_ADMIN, 
                            None, [TRANSFER_REQUESTED])
ACTION_ACKNOWLEDGED = model.StateAction('ack', 'Received', RoleType.PAYMENT_ADMIN, None, [TRANSFER_TRANSFERRED])

class RequestTotalsField(readonly_fields.ReadOnlyField):
    def __init__(self, name):
        super(RequestTotalsField, self).__init__(name)

    def render_value(self, transfer):
        total_sterling = 0
        total_shillings = 0
        for grant in transfer.grant_list:
            if grant.amount.currency == 'sterling':
                total_sterling += grant.amount.value
            else:
                total_shillings += grant.amount.value
        return u"£{:,} + {:,} Ush".format(total_sterling, total_shillings)

ref_field = readonly_fields.ReadOnlyField('ref_id')
state_field = readonly_fields.StateField('Closed', 'Requested', 'Transferred')
creator_field = readonly_fields.ReadOnlyKeyField('creator')
creation_date_field = readonly_fields.ReadOnlyField('creation_date')
rate_field = readonly_fields.ReadOnlyField('exchange_rate')
request_totals_field = RequestTotalsField('total_payment')

class ExchangeRateForm(wtforms.Form):
    action = wtforms.HiddenField(default='transferred')
    exchange_rate = wtforms.IntegerField('Exchange Rate', validators=[wtforms.validators.InputRequired()])
        
@app.route('/foreigntransfer_list/<db_id>')
def view_foreigntransfer_list(db_id):
    supplier = model.lookup_entity(db_id)
    breadcrumbs = views.create_breadcrumbs(supplier)
    transfer_list = db.ForeignTransfer.query(ancestor=supplier.key).fetch()
    transfer_fields = [creation_date_field, ref_field, state_field, rate_field]
    entity_table = renderers.render_table(transfer_list, views.url_for_entity, *transfer_fields)
    return views.render_view('Foreign Transfer List', breadcrumbs, entity_table)

def process_transferred_button(transfer, user, buttons):
    form = ExchangeRateForm(request.form)
    if (request.method == 'POST' and request.form.get('action') == 'transferred' 
              and form.validate()):
        form.populate_obj(transfer)
        transfer.state_index = TRANSFER_TRANSFERRED
        transfer.put()
        grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
        for grant in grant_list:
            grant.state_index = grants.GRANT_TRANSFERED
            grant.put()
        return True
    enabled = ACTION_TRANSFERRED.is_allowed(transfer, user)
    button = custom_fields.render_dialog_button(ACTION_TRANSFERRED.label, 'd-transferred', form, enabled)
    buttons.append(button)
    return False

def do_acknowledge(transfer):
    transfer.state_index = TRANSFER_CLOSED
    transfer.put()
    grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
    for grant in grant_list:
        project = grant.project.get()
        if project.partner is None:
            grant.state_index = grants.GRANT_CLOSED
            grant.put()
    
@app.route('/foreigntransfer/<db_id>', methods=['GET', 'POST'])        
def view_foreigntransfer(db_id):
    transfer = model.lookup_entity(db_id)
    if transfer.creation_date is None:
        transfer.creation_date = date(2019, 2, 8)
        transfer.put()
    user = views.current_user()
    buttons = []
    if process_transferred_button(transfer, user, buttons):
        return redirect(request.base_url)
    if views.process_action_button(ACTION_ACKNOWLEDGED, transfer, user, buttons):
        do_acknowledge(transfer)
        return redirect(request.base_url)
    transfer_fields = (creation_date_field, ref_field, state_field, rate_field, request_totals_field, creator_field)
    breadcrumbs = views.create_breadcrumbs_list(transfer)
    grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
    transfer.grant_list = grant_list
    grid = renderers.render_grid(transfer, transfer_fields)
    payments = paymentsdue.render_payments(grant_list)
    sub_heading = renderers.sub_heading('Grant Payments')
    content = (grid, sub_heading, payments)
    return views.render_view('Foreign Transfer', breadcrumbs, content, buttons=buttons)
