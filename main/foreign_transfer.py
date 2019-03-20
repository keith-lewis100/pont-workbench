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
import purchases

TRANSFER_CLOSED = 0
TRANSFER_REQUESTED = 1
TRANSFER_TRANSFERRED = 2

ACTION_TRANSFERRED = model.StateAction('transferred', 'Transferred', RoleType.PAYMENT_ADMIN, 
                            None, [TRANSFER_REQUESTED])
ACTION_ACKNOWLEDGED = model.StateAction('ack', 'Received', RoleType.PAYMENT_ADMIN, None, [TRANSFER_TRANSFERRED])

class RequestTotalsField(readonly_fields.ReadOnlyField):
    def get_value(self, transfer, no_links):
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

grant_field_list = [
    grants.state_field, grants.creator_field, grants.project_field, grants.amount_field,
    grants.transferred_amount_field,
    readonly_fields.ReadOnlyField('project.partner.name', 'Implementing Partner'),
    grants.source_field,
    readonly_fields.ReadOnlyField('project.^.name', 'Destination Fund')
]

advance_field_list = (purchases.advance_type_field, purchases.po_number_field, purchases.creator_field, grants.source_field, 
                      purchases.advance_amount_field)
invoice_field_list = (purchases.invoice_type_field, purchases.po_number_field, purchases.creator_field, grants.source_field,
                           purchases.invoiced_amount_field)

class ExchangeRateForm(wtforms.Form):
    exchange_rate = wtforms.IntegerField('Exchange Rate', validators=[wtforms.validators.InputRequired()])
        
@app.route('/foreigntransfer_list/<db_id>')
def view_foreigntransfer_list(db_id):
    supplier = model.lookup_entity(db_id)
    breadcrumbs = views.create_breadcrumbs(supplier)
    transfer_list = db.ForeignTransfer.query(ancestor=supplier.key).fetch()
    transfer_fields = [creation_date_field, ref_field, state_field, rate_field]
    entity_table = views.render_entity_list(transfer_list, transfer_fields)
    return views.render_view('Foreign Transfer List', breadcrumbs, entity_table)

def process_transferred_button(transfer, user, buttons):
    form = ExchangeRateForm(request.form)
    if (request.method == 'POST' and request.form.get('_action') == 'transferred' 
              and form.validate()):
        form.populate_obj(transfer)
        transfer.state_index = TRANSFER_TRANSFERRED
        transfer.put()
        grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
        for grant in grant_list:
            grant.state_index = grants.GRANT_TRANSFERED
            grant.put()
        ACTION_TRANSFERRED.audit(transfer, user)
        return True
    enabled = ACTION_TRANSFERRED.is_allowed(transfer, user)
    button = custom_fields.render_dialog_button(ACTION_TRANSFERRED.label, 'transferred', form, enabled)
    buttons.append(button)
    return False

def do_acknowledge(transfer, user):
    transfer.state_index = TRANSFER_CLOSED
    transfer.put()
    grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
    for grant in grant_list:
        project = grant.project.get()
        if project.partner is None:
            grant.state_index = grants.GRANT_CLOSED
            grant.put()
    ACTION_ACKNOWLEDGED.audit(transfer, user)

def render_grants_due_list(grant_list):
    sub_heading = renderers.sub_heading('Grant Payments')
    table = views.render_entity_list(grant_list, grant_field_list)
    return (sub_heading, table)

def render_purchase_payments_list(transfer):
    column_headers = readonly_fields.get_labels(advance_field_list)
    
    advance_list = db.Purchase.query(db.Purchase.advance.transfer == transfer.key).fetch()
    advance_grid = readonly_fields.display_entity_list(advance_list, advance_field_list, no_links=True)
    advance_url_list = map(readonly_fields.url_for_entity, advance_list)
    
    invoice_list = db.Purchase.query(db.Purchase.invoice.transfer == transfer.key).fetch()
    invoice_grid = readonly_fields.display_entity_list(invoice_list, invoice_field_list, no_links=True)
    invoice_url_list = map(readonly_fields.url_for_entity, invoice_list)
    
    sub_heading = renderers.sub_heading('Purchase Payments')
    table = renderers.render_table(column_headers, advance_grid + invoice_grid,
                            advance_url_list + invoice_url_list)
    return (sub_heading, table)

@app.route('/foreigntransfer/<db_id>', methods=['GET', 'POST'])        
def view_foreigntransfer(db_id):
    transfer = model.lookup_entity(db_id)
    user = views.current_user()
    buttons = []
    if process_transferred_button(transfer, user, buttons):
        return redirect(request.base_url)
    if views.process_action_button(ACTION_ACKNOWLEDGED, transfer, user, buttons):
        do_acknowledge(transfer, user)
        return redirect(request.base_url)
    transfer_fields = (creation_date_field, ref_field, state_field, rate_field, request_totals_field, creator_field)
    breadcrumbs = views.create_breadcrumbs_list(transfer)
    grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
    transfer.grant_list = grant_list
    grid = views.render_entity(transfer, transfer_fields)
    grant_payments = render_grants_due_list(grant_list)
#    purchase_payments = render_purchase_payments_list(transfer)
    history = views.render_entity_history(transfer.key)
    content = (grid, grant_payments, history)
    return views.render_view('Foreign Transfer', breadcrumbs, content, buttons=buttons)
