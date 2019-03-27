#_*_ coding: UTF-8 _*_

from flask import request, redirect, url_for
from application import app
import datetime
import wtforms

import db
import data_models
import renderers
import custom_fields
import properties
import views
from role_types import RoleType
import grants
import purchases

class SupplierForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    receives_grants = wtforms.BooleanField()
    paid_in_sterling = wtforms.BooleanField()

ACTION_TRANSFER_START = views.Action('startTransfer', 'Request Foreign Transfer', RoleType.PAYMENT_ADMIN)
ACTION_CREATE = views.create_action(RoleType.SUPPLIER_ADMIN)
ACTION_UPDATE = views.update_action(RoleType.SUPPLIER_ADMIN)

@app.route('/supplier_list', methods=['GET', 'POST'])
def view_supplier_list():
    new_supplier = db.Supplier()
    form = SupplierForm(request.form, obj=new_supplier)
    model = data_models.Model(None)
    model.add_form('create', form)
    if request.method == 'POST' and form.validate():
        form.populate_obj(new_supplier)
        ACTION_CREATE.apply_to(new_supplier, model.user)
        ACTION_CREATE.audit(new_supplier, model.user)
        return redirect(request.base_url)
    
    breadcrumbs = views.create_breadcrumbs(None)
    supplier_field_list = (properties.StringProperty('name'), )
    supplier_list = db.Supplier.query().fetch()
    entity_table = views.render_entity_list(supplier_list, supplier_field_list)
    buttons = views.view_actions([ACTION_CREATE], model, None)
    return views.render_view('Supplier List', breadcrumbs, entity_table, buttons=buttons)

def get_links(supplier):
    db_id = supplier.key.urlsafe()
    links = []
    if supplier.receives_grants:
        showFunds = views.render_link('SupplierFund', 'Show Supplier Funds', supplier)
        showPartners = views.render_link('Partners', 'Show Partners', supplier)
        links = [showFunds, showPartners]
    if supplier.paid_in_sterling:
        return links
    return links + [views.render_link('ForeignTransfer', 'Show Foreign Transfers', supplier)]

def create_transfer(supplier, user):
    transfer = db.ForeignTransfer(parent=supplier.key)
    transfer.creator = user.key
    ref = data_models.get_next_ref()
    transfer.ref_id = 'FT%04d' % ref
    transfer.put()
    return transfer

def process_transfer_request(supplier, user):
    grant_list = db.find_ready_payments(supplier)
    if len(grant_list) == 0:
        return None
    transfer = create_transfer(supplier, user)
    for grant in grant_list:
        if getattr(grant, 'transfer', None) is None:
            grant.transfer = transfer.key
            grant.put()
    ACTION_TRANSFER_START.audit(transfer, user)
    return transfer

def render_grants_due_list(supplier):
    cutoff_date = datetime.date.today() + datetime.timedelta(21)
    grant_list = db.find_pending_payments(supplier, cutoff_date)
    field_list = (grants.state_field, grants.target_date_field, grants.creator_field, grants.source_field, grants.project_field, grants.amount_field)
    sub_heading = renderers.sub_heading('Grant Payments Due')
    table = views.render_entity_list(grant_list, field_list)
    return (sub_heading, table)
    
common_field_list = [purchases.advance_type_field, purchases.po_number_field, purchases.creator_field,
       grants.source_field]
advance_field_list = common_field_list + [purchases.advance_amount_field]
invoice_field_list = common_field_list + [purchases.invoiced_amount_field]

def render_purchase_payments_list(supplier):
    column_headers = properties.get_labels(advance_field_list)
    
    advance_list = db.Purchase.query(db.Purchase.supplier == supplier.key).filter(
                         db.Purchase.advance.paid == False).fetch()
    advance_grid = properties.display_entity_list(advance_list, advance_field_list, no_links=True)
    advance_url_list = map(properties.url_for_entity, advance_list)
    
    invoice_list = db.Purchase.query(db.Purchase.supplier == supplier.key).filter(
                         db.Purchase.invoice.paid == False).fetch()
    invoice_grid = properties.display_entity_list(invoice_list, invoice_field_list, no_links=True)
    invoice_url_list = map(properties.url_for_entity, invoice_list)
    
    sub_heading = renderers.sub_heading('Purchase Payments Due')
    table = renderers.render_table(column_headers, advance_grid + invoice_grid,
                            advance_url_list + invoice_url_list)
    return (sub_heading, table)

@app.route('/supplier/<db_id>', methods=['GET', 'POST'])
def view_supplier(db_id):
    supplier = data_models.lookup_entity(db_id)
    form = SupplierForm(request.form, obj=supplier)
    model = data_models.Model(supplier, None)
    model.add_form('update', form)
    if views.process_edit_button(ACTION_UPDATE, form, supplier):
        return redirect(request.base_url)
    error = ""
    if not supplier.paid_in_sterling and views.process_action_button(ACTION_TRANSFER_START, model, supplier):
        transfer = process_transfer_request(supplier, model.user)
        if transfer is not None:
            transfer_url = views.url_for_entity(transfer)
            return redirect(transfer_url)
        error = renderers.render_error("No grants are pending - nothing to transfer")
    breadcrumbs = views.create_breadcrumbs_list(supplier)
    links = get_links(supplier)
    fields = (properties.StringProperty('name'), )
    grid = views.render_entity(supplier, fields)
    title = 'Supplier ' + supplier.name
    purchase_payments = render_purchase_payments_list(supplier)
    content = [error, grid, purchase_payments]
    if supplier.receives_grants:
        grant_payments = render_grants_due_list(supplier)
        content.append(grant_payments)
    content.append(views.render_entity_history(supplier.key))
    buttons = views.view_actions([ACTION_UPDATE, ACTION_TRANSFER_START], model, supplier)
    return views.render_view(title, breadcrumbs, content, links=links, buttons=buttons)
