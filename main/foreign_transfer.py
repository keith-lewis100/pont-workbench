#_*_ coding: UTF-8 _*_

from flask import request, redirect, render_template
from application import app
import wtforms
import logging
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, HtmlContent

import db
import data_models
import renderers
import properties
import views
from role_types import RoleType
import urls

import grants
import purchases

STATE_REQUESTED = 1
STATE_TRANSFERRED = 2

state_labels = ['Closed', 'Requested', 'Transferred']

def perform_transferred(model, action_name):
    form = model.get_form(action_name)
    if not form.validate():
        return False
    transfer = model.entity
    form.populate_obj(transfer)
    transfer.state_index = STATE_TRANSFERRED
    transfer.put()
    payment_list = db.PurchasePayment.query(db.PurchasePayment.transfer == transfer.key).fetch()
    for payment in payment_list:
        payment.paid = True
        payment.put()
        if payment.payment_type == 'invoice':
            purchase = data_models.get_parent(payment)
            purchase.state_index = data_models.STATE_CLOSED
            purchase.put()
    model.audit(action_name, 'Transfer performed')
    send_supplier_email(transfer)
    return True

def perform_ack(model, action_name):
    model.perform_close(action_name)
    transfer = model.entity
    grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
    for grant in grant_list:
        project = grant.project.get()
        if project.partner is None:
            grant.state_index = data_models.STATE_CLOSED
            grant.put()
            model.audit(action_name, 'Transfer received', grant)
    return True

ACTION_TRANSFERRED = views.StateAction('transferred', 'Transferred', RoleType.PAYMENT_ADMIN, 
                            perform_transferred, [STATE_REQUESTED])
ACTION_ACKNOWLEDGED = views.StateAction('ack', 'Received', RoleType.PAYMENT_ADMIN,
                                        perform_ack, [STATE_TRANSFERRED])

action_list = [ACTION_TRANSFERRED, ACTION_ACKNOWLEDGED]

def calculate_totals(transfer):
    total_sterling = 0
    total_shillings = 0
    for p in transfer.grant_list + transfer.payment_list:
        if p.amount.currency == 'sterling':
            total_sterling += p.amount.value
        else:
            total_shillings += p.amount.value
    return (total_sterling, total_shillings)

def show_totals(transfer):
    sterling, shillings = calculate_totals(transfer)
    return u"£{:,} + {:,} Ush".format(sterling, shillings)

def show_shillings(transfer):
    sterling, shillings = calculate_totals(transfer)
    total_shillings = int(sterling * transfer.exchange_rate) + shillings
    return u"{:,} Ush".format(total_shillings)

ref_field = properties.StringProperty('ref_id')
state_field = properties.SelectProperty('state_index', 'State', enumerate(state_labels))
creator_field = properties.KeyProperty('creator')
creation_date_field = properties.DateProperty('creation_date')
rate_field = properties.StringProperty('exchange_rate')
request_totals_field = properties.StringProperty(show_totals, 'Request Totals')
shillings_total_field = properties.StringProperty(show_shillings, 'Transfered Amount')

def get_partner(grant):
    project = grant.project.get()
    if project.partner:
        return project.partner.get().name
    return ""

grant_field_list = [
    grants.state_field, grants.creator_field, grants.project_field, grants.amount_field,
    grants.transferred_amount_field,
    properties.StringProperty(get_partner, 'Implementing Partner'),
    grants.source_field,
    properties.StringProperty(lambda e: e.project.parent().get().name, 'Destination Fund')
]

po_number_field = properties.StringProperty(lambda e: e.key.parent().get().po_number, 'PO Number')
requestor_field = properties.KeyProperty(lambda e: e.key.parent().get().creator, 'Requestor')
source_field = properties.StringProperty(lambda e: e.key.parent().parent().get().code, 'Source Fund')
payment_field_list = [purchases.payment_type_field, po_number_field, requestor_field, source_field,
        purchases.payment_amount_field]

class ExchangeRateForm(wtforms.Form):
    exchange_rate = wtforms.IntegerField('Exchange Rate', validators=[wtforms.validators.InputRequired()])
        
@app.route('/foreigntransfer_list/<db_id>')
def view_foreigntransfer_list(db_id):
    supplier = data_models.lookup_entity(db_id)
    model = data_models.Model(None, None)
    breadcrumbs = views.view_breadcrumbs(supplier)
    transfer_list = db.ForeignTransfer.query(ancestor=supplier.key).order(db.ForeignTransfer.ref_id).fetch()
    transfer_fields = [creation_date_field, ref_field, state_field, rate_field]
    entity_table = views.view_entity_list(transfer_list, transfer_fields)
    user_controls = views.view_user_controls(model)
    return render_template('layout.html', title='Foreign Transfer List', breadcrumbs=breadcrumbs,
                           user=user_controls, content=entity_table)

def render_grants_due_list(grant_list, selectable=True, no_links=True):
    sub_heading = renderers.sub_heading('Grant Payments')
    table = views.view_entity_list(grant_list, grant_field_list, selectable, no_links)
    return (sub_heading, table)

def render_purchase_payments_list(payment_list):
    column_headers = properties.get_labels(payment_field_list)
    payment_grid = properties.display_entity_list(payment_list, payment_field_list, no_links=True)
    purchase_list = [data_models.get_parent(e) for e in payment_list]
    payment_url_list = map(urls.url_for_entity, purchase_list)
    
    sub_heading = renderers.sub_heading('Purchase Payments')
    table = renderers.render_table(column_headers, payment_grid,
                            payment_url_list)
    return (sub_heading, table)

@app.route('/foreigntransfer/<db_id>', methods=['GET', 'POST'])        
def view_foreigntransfer(db_id):
    transfer = data_models.lookup_entity(db_id)
    grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
    transfer.grant_list = grant_list
    payment_list = db.PurchasePayment.query(db.PurchasePayment.transfer == transfer.key).fetch()
    transfer.payment_list = payment_list
    supplier = data_models.get_parent(transfer)
    form = ExchangeRateForm(request.form)
    model = data_models.Model(transfer, None)
    model.add_form(ACTION_TRANSFERRED.name, form)
    if request.method == 'POST'and views.handle_post(model, action_list):
        return redirect(request.base_url)
    transfer_fields = (creation_date_field, ref_field, state_field, rate_field, request_totals_field, creator_field)
    breadcrumbs = views.view_breadcrumbs(supplier, 'ForeignTransfer')
    grid = views.view_entity(transfer, transfer_fields)
    grant_payments = render_grants_due_list(grant_list)
    purchase_payments = render_purchase_payments_list(payment_list)
    history = views.view_entity_history(transfer.key)
    content = renderers.render_div(grid, purchase_payments, grant_payments, history)
    buttons = views.view_actions(action_list, model)
    user_controls = views.view_user_controls(model)
    return render_template('layout.html', title='Foreign Transfer', breadcrumbs=breadcrumbs, user=user_controls,
                           buttons=buttons, content=content)

email_properties = (ref_field, shillings_total_field)

def send_supplier_email(transfer):
    supplier = data_models.get_parent(transfer)
    column = views.view_entity_single_column(transfer, email_properties)
    grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
    grant_payments = render_grants_due_list(grant_list, selectable=False, no_links=True)
    content = renderers.render_div(column, grant_payments)
    html = render_template('email.html', title='Foreign Transfer', content=content)
    message = Mail(
        from_email='workbench@pont-mbale.org.uk',
        to_emails=str(','.join(supplier.contact_emails)),
        subject='Foreign Transfer',
        html_content=HtmlContent(html)
    )
    workbench = db.WorkBench.query().get()
    sg = SendGridAPIClient(workbench.email_api_key)
    response = sg.send(message)
    if response.status_code > 299:
        logging.error('unable to send email for transfer: %s status: %d' % (transfer.ref_id, response.status_code))
    else:
        logging.info('sent email for transfer: %s' % transfer.ref_id)
