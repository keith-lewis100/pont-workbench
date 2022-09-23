#_*_ coding: UTF-8 _*_

from flask import request, redirect, render_template
from application import app
import wtforms

import db
import data_models
import mailer
import renderers
import properties
import views
from role_types import RoleType
import urls

from . import grants
from . import purchases

STATE_REQUESTED = 1
STATE_TRANSFERRED = 2

state_labels = ['Closed', 'Requested', 'Transferred']

class TransferModel(data_models.Model):
    def __init__(self, entity, grant_list, payment_list):
        super(TransferModel, self).__init__(entity, None)
        self.grant_list = grant_list
        self.payment_list = payment_list

    def perform_transferred(self, action_name):
        form = self.get_form(action_name)
        if not form.validate():
            return False
        transfer = self.entity
        form.populate_obj(transfer)
        transfer.state_index = STATE_TRANSFERRED
        transfer.put()
        parent_audit = self.audit(action_name, 'Transfer performed')
        for payment in self.payment_list:
            payment.paid = True
            payment.put()
            purchase = data_models.get_parent(payment)
            if payment.payment_type == 'invoice':
                purchase.state_index = data_models.STATE_CLOSED
                purchase.put()
            self.audit(action_name, 'Payment transferred', purchase, parent_audit.key)
            data_models.email_entity_creator(purchase, self.user, 'Payment transferred')
        for grant in self.grant_list:
            data_models.email_entity_creator(grant, self.user, 'Transfer performed')
        self.send_supplier_email()
        return True

    def send_supplier_email(self):
        transfer = self.entity
        supplier = data_models.get_parent(transfer)
        column = views.view_entity_single_column(transfer, email_properties)
        purchase_payments = render_purchase_payments_list(self.payment_list)
        grant_payments = render_grants_due_list(self.grant_list, selectable=False)
        content = renderers.render_div(column, purchase_payments, grant_payments)
        mailer.send_email('PONT Transfer %s' % transfer.ref_id, content, supplier.contact_emails)

    def perform_ack(self, action_name):
        parent_audit = self.perform_close(action_name)
        transfer = self.entity
        for grant in self.grant_list:
            project = grant.project.get()
            if project.partner is None:
                grant.state_index = data_models.STATE_CLOSED
                grant.put()
                self.audit(action_name, 'Transfer acknowledged', grant, parent_audit.key)
                data_models.email_entity_creator(grant, self.user, 'Transfer acknowledged')
        return True

ACTION_TRANSFERRED = views.StateAction('transferred', 'Transferred', RoleType.PAYMENT_ADMIN, 
                            TransferModel.perform_transferred, [STATE_REQUESTED])
ACTION_ACKNOWLEDGED = views.StateAction('ack', 'Received', RoleType.PAYMENT_ADMIN,
                                        TransferModel.perform_ack, [STATE_TRANSFERRED])

action_list = [ACTION_TRANSFERRED, ACTION_ACKNOWLEDGED]

def show_totals(transfer):
    sterling, shillings = transfer.totals
    return u"£{:,} + {:,} Ush".format(sterling, shillings)

def show_shillings(transfer):
    if not transfer.exchange_rate:
        return ""
    sterling, shillings = transfer.totals
    total_shillings = int(sterling * transfer.exchange_rate) + shillings
    return u"{:,} Ush".format(total_shillings)

ref_field = properties.StringProperty('ref_id')
state_field = properties.SelectProperty('state_index', 'State', enumerate(state_labels))
creator_field = properties.KeyProperty('creator')
creation_date_field = properties.DateProperty('creation_date', format='%Y-%m-%d')
rate_field = properties.StringProperty('exchange_rate')
request_totals_field = properties.StringProperty(show_totals, 'Request Totals')
shillings_total_field = properties.StringProperty(show_shillings, 'Total Amount')

def get_partner(grant):
    project = grant.project.get()
    if project.partner:
        return project.partner.get().name
    return ""

grant_field_list = (
    grants.state_field, grants.creator_field, grants.project_field, grants.amount_field,
    grants.transferred_amount_field,
    properties.StringProperty(get_partner, 'Implementing Partner'),
    grants.source_field,
    properties.StringProperty(lambda e: e.project.get().fund.get().name, 'Destination Fund')
)

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
    dummy_transfer = db.ForeignTransfer(parent=supplier.key)
    model = data_models.Model(dummy_transfer, None)
    breadcrumbs = views.view_breadcrumbs(supplier)
    transfer_fields = [state_field, ref_field, creation_date_field, rate_field]
    model.show_closed = request.args.has_key('show_closed')
    db_filter = db.ForeignTransfer.state_index == 0 if model.show_closed else db.ForeignTransfer.state_index > 0
    entity_list = db.ForeignTransfer.query(ancestor=supplier.key).filter(db_filter).fetch()
    entity_list.sort(reverse=True, key=lambda e: e.ref_id)
    entity_table = views.view_entity_list(entity_list, transfer_fields)
    buttons = views.view_actions([views.ACTION_FILTER], model)
    user_controls = views.view_user_controls(model)
    return render_template('layout.html', title='Foreign Transfer List', breadcrumbs=breadcrumbs,
                           user=user_controls, buttons=buttons, content=entity_table)

def render_grants_due_list(grant_list, selectable=True):
    sub_heading = renderers.sub_heading('Grant Payments')
    table = views.view_entity_list(grant_list, grant_field_list, wide_field=grants.description_field)
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

def calculate_totals(payments):
    total_sterling = 0
    total_shillings = 0
    for p in payments:
        if p.amount.currency == 'sterling':
            total_sterling += p.amount.value
        else:
            total_shillings += p.amount.value
    return (total_sterling, total_shillings)

@app.route('/foreigntransfer/<db_id>', methods=['GET', 'POST'])        
def view_foreigntransfer(db_id):
    transfer = data_models.lookup_entity(db_id)
    grant_list = db.Grant.query(db.Grant.transfer == transfer.key).fetch()
    payment_list = db.PurchasePayment.query(db.PurchasePayment.transfer == transfer.key).fetch()
    transfer.totals = calculate_totals(grant_list + payment_list)
    form = ExchangeRateForm(request.form)
    model = TransferModel(transfer, grant_list, payment_list)
    model.add_form(ACTION_TRANSFERRED.name, form)
    if request.method == 'POST'and views.handle_post(model, action_list):
        return redirect(request.base_url)
    transfer_fields = (creation_date_field, ref_field, state_field, rate_field, request_totals_field,
                       shillings_total_field, creator_field)
    breadcrumbs = views.view_breadcrumbs_list(transfer)
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

