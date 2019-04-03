#_*_ coding: UTF-8 _*_

from flask import url_for, request, redirect
from application import app
import wtforms
from datetime import date

import db
import data_models
import renderers
import properties
import views
from role_types import RoleType
import urls

import grants
import purchases

TRANSFER_CLOSED = 0
TRANSFER_REQUESTED = 1
TRANSFER_TRANSFERRED = 2

state_labels = ['Closed', 'Requested', 'Transferred']
def state_of(entity):
    return state_labels[entity.state_index]

ACTION_TRANSFERRED = views.StateAction('transferred', 'Transferred', RoleType.PAYMENT_ADMIN, 
                            [TRANSFER_REQUESTED])
ACTION_ACKNOWLEDGED = views.StateAction('ack', 'Received', RoleType.PAYMENT_ADMIN, [TRANSFER_TRANSFERRED])

def calculate_totals(transfer):
    total_sterling = 0
    total_shillings = 0
    for grant in transfer.grant_list:
        if grant.amount.currency == 'sterling':
            total_sterling += grant.amount.value
        else:
            total_shillings += grant.amount.value
    return u"£{:,} + {:,} Ush".format(total_sterling, total_shillings)

ref_field = properties.StringProperty('ref_id')
state_field = properties.StringProperty(state_of, 'State')
creator_field = properties.KeyProperty('creator')
creation_date_field = properties.DateProperty('creation_date')
rate_field = properties.StringProperty('exchange_rate')
request_totals_field = properties.StringProperty(calculate_totals, 'Request Totals')

grant_field_list = [
    grants.state_field, grants.creator_field, grants.project_field, grants.amount_field,
    grants.transferred_amount_field,
    properties.StringProperty('project.partner.name', 'Implementing Partner'),
    grants.source_field,
    properties.StringProperty('project.^.name', 'Destination Fund')
]

advance_field_list = (purchases.advance_type_field, purchases.po_number_field, purchases.creator_field, grants.source_field, 
                      purchases.advance_amount_field)
invoice_field_list = (purchases.invoice_type_field, purchases.po_number_field, purchases.creator_field, grants.source_field,
                           purchases.invoiced_amount_field)

class ExchangeRateForm(wtforms.Form):
    exchange_rate = wtforms.IntegerField('Exchange Rate', validators=[wtforms.validators.InputRequired()])
        
@app.route('/foreigntransfer_list/<db_id>')
def view_foreigntransfer_list(db_id):
    supplier = data_models.lookup_entity(db_id)
    breadcrumbs = views.view_breadcrumbs(supplier)
    transfer_list = db.ForeignTransfer.query(ancestor=supplier.key).fetch()
    transfer_fields = [creation_date_field, ref_field, state_field, rate_field]
    entity_table = views.render_entity_list(transfer_list, transfer_fields)
    user_controls = views.view_user_controls(model)
    return views.render_view('Foreign Transfer List', user_controls, breadcrumbs, entity_table)

def process_transferred_button(model, transfer):
    form = model.get_form(ACTION_TRANSFERRED.name)
    if (request.method == 'POST' and request.form.get('_action') == ACTION_TRANSFERRED.name 
              and form.validate()):
        form.populate_obj(transfer)
        transfer.state_index = TRANSFER_TRANSFERRED
        transfer.put()
        grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
        for grant in grant_list:
            grant.state_index = grants.GRANT_TRANSFERED
            grant.put()
        ACTION_TRANSFERRED.audit(transfer, model.user)
        return True
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
    column_headers = properties.get_labels(advance_field_list)
    
    advance_list = db.Purchase.query(db.Purchase.advance.transfer == transfer.key).fetch()
    advance_grid = properties.display_entity_list(advance_list, advance_field_list, no_links=True)
    advance_url_list = map(urls.url_for_entity, advance_list)
    
    invoice_list = db.Purchase.query(db.Purchase.invoice.transfer == transfer.key).fetch()
    invoice_grid = properties.display_entity_list(invoice_list, invoice_field_list, no_links=True)
    invoice_url_list = map(urls.url_for_entity, invoice_list)
    
    sub_heading = renderers.sub_heading('Purchase Payments')
    table = renderers.render_table(column_headers, advance_grid + invoice_grid,
                            advance_url_list + invoice_url_list)
    return (sub_heading, table)

@app.route('/foreigntransfer/<db_id>', methods=['GET', 'POST'])        
def view_foreigntransfer(db_id):
    transfer = data_models.lookup_entity(db_id)
    form = ExchangeRateForm(request.form)
    model = data_models.Model(transfer, None)
    model.add_form(ACTION_TRANSFERRED.name, form)
    if process_transferred_button(model, transfer):
        return redirect(request.base_url)
    if views.process_action_button(ACTION_ACKNOWLEDGED, model, transfer):
        do_acknowledge(transfer, model.user)
        return redirect(request.base_url)
    transfer_fields = (creation_date_field, ref_field, state_field, rate_field, request_totals_field, creator_field)
    breadcrumbs = views.view_breadcrumbs(transfer, True)
    grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
    transfer.grant_list = grant_list
    grid = views.render_entity(transfer, transfer_fields)
    grant_payments = render_grants_due_list(grant_list)
#    purchase_payments = render_purchase_payments_list(transfer)
    history = views.render_entity_history(transfer.key)
    content = (grid, grant_payments, history)
    buttons = views.view_actions([ACTION_TRANSFERRED, ACTION_ACKNOWLEDGED], model, transfer)
    user_controls = views.view_user_controls(model)
    return views.render_view('Foreign Transfer', user_controls, breadcrumbs, content, buttons=buttons)
