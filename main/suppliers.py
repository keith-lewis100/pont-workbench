#_*_ coding: UTF-8 _*_

from flask import request, redirect, render_template
from application import app
import datetime
import wtforms

import db
import data_models
import renderers
import properties
import views
from role_types import RoleType
import urls

import grants
import purchases

class SupplierForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    receives_grants = wtforms.BooleanField()
    paid_in_sterling = wtforms.BooleanField()

def perform_create_transfer(model, action_name):
    supplier = model.entity
    grant_list = db.find_ready_payments(supplier)
    if len(grant_list) == 0:
        return None
    transfer = create_transfer(supplier, user)
    for grant in grant_list:
        if getattr(grant, 'transfer', None) is None:
            grant.transfer = transfer.key
            grant.put()
    model.audit(action_name, 'Transfer started')
    return True

ACTION_TRANSFER_START = views.Action('startTransfer', 'Request Foreign Transfer', RoleType.PAYMENT_ADMIN,
                                     perform_create_transfer)
ACTION_CREATE = views.create_action(RoleType.SUPPLIER_ADMIN)
ACTION_UPDATE = views.update_action(RoleType.SUPPLIER_ADMIN)

@app.route('/supplier_list', methods=['GET', 'POST'])
def view_supplier_list():
    new_supplier = db.Supplier()
    form = SupplierForm(request.form, obj=new_supplier)
    model = data_models.Model(new_supplier, None)
    model.add_form('create', form)
    property_list = (properties.StringProperty('name'), )
    supplier_list = db.Supplier.query().fetch()
    return views.view_std_entity_list(model, 'Supplier List', ACTION_CREATE, property_list,
                                      supplier_list)

def get_link_pairs(supplier):
    links = []
    if supplier.receives_grants:
        links = [('SupplierFund', 'Show Supplier Funds'), ('Partners', 'Show Partners')]
    if supplier.paid_in_sterling:
        return links
    return links + [('ForeignTransfer', 'Show Foreign Transfers')]

def create_transfer(supplier, user):
    transfer = db.ForeignTransfer(parent=supplier.key)
    transfer.creator = user.key
    ref = data_models.get_next_ref()
    transfer.ref_id = 'FT%04d' % ref
    transfer.put()
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
    advance_url_list = map(urls.url_for_entity, advance_list)
    
    invoice_list = db.Purchase.query(db.Purchase.supplier == supplier.key).filter(
                         db.Purchase.invoice.paid == False).fetch()
    invoice_grid = properties.display_entity_list(invoice_list, invoice_field_list, no_links=True)
    invoice_url_list = map(urls.url_for_entity, invoice_list)
    
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
    valid_actions = [ACTION_UPDATE]
    if not supplier.paid_in_sterling:
        valid_actions.append(ACTION_TRANSFER_START)
    if request.method == 'POST'  and views.handle_post(model, valid_actions):
        return redirect(request.base_url)
    error = ""
##    if not supplier.paid_in_sterling and views.process_action_button(ACTION_TRANSFER_START, model, supplier):
##        transfer = process_transfer_request(supplier, model.user)
##        if transfer is not None:
##            transfer_url = urls.url_for_entity(transfer)
##            return redirect(transfer_url)
##        error = renderers.render_error("No grants are pending - nothing to transfer")
    breadcrumbs = views.create_breadcrumbs_list(supplier)
    links = views.view_links(supplier, *get_link_pairs(supplier))
    fields = (properties.StringProperty('name'), )
    grid = views.view_entity(supplier, fields)
    title = 'Supplier ' + supplier.name
    purchase_payments = render_purchase_payments_list(supplier)
    content_list = [error, grid, purchase_payments]
    if supplier.receives_grants:
        grant_payments = render_grants_due_list(supplier)
        content_list.append(grant_payments)
    content_list.append(views.view_entity_history(supplier.key))
    buttons = views.view_actions(valid_actions, model, supplier)
    content = renderers.render_div(*content_list)
    user_controls = views.view_user_controls(model)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbs, user=user_controls,
                           links=links, buttons=buttons, content=content)
