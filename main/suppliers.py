#_*_ coding: UTF-8 _*_

from flask import request, redirect, url_for
from application import app
from flask.views import View
import datetime
import wtforms

import db
import model
import renderers
import custom_fields
import readonly_fields
import views
from role_types import RoleType
import grants
import purchases

class SupplierForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    receives_grants = wtforms.BooleanField()
    paid_in_sterling = wtforms.BooleanField()

start_transfer = model.Action('startTransfer', 'Request Foreign Transfer', RoleType.PAYMENT_ADMIN)
create_action = model.Action('create', 'New', RoleType.SUPPLIER_ADMIN)
update_action = model.Action('update', 'Edit', RoleType.SUPPLIER_ADMIN)

@app.route('/supplier_list', methods=['GET', 'POST'])
def view_supplier_list():
    user = views.current_user()
    new_supplier = db.Supplier()
    form = SupplierForm(request.form, obj=new_supplier)
    enabled = create_action.is_allowed(None, user)
    if request.method == 'POST' and form.validate():
        form.populate_obj(new_supplier)
        new_supplier.put()
        return redirect(request.base_url)
        
    new_button = custom_fields.render_dialog_button('New', 'm1', form, enabled)
    breadcrumbs = views.create_breadcrumbs(None)
    supplier_field_list = (readonly_fields.ReadOnlyField('name'), )
    supplier_list = db.Supplier.query().fetch()
    entity_table = readonly_fields.render_table(supplier_list, supplier_field_list)
    return views.render_view('Supplier List', breadcrumbs, entity_table, buttons=[new_button])

def get_links(supplier):
    db_id = supplier.key.urlsafe()
    links = []
    if supplier.receives_grants:
        funds_url = url_for('view_supplierfund_list', db_id=db_id)
        showFunds = renderers.render_link('Show Funds', funds_url, class_="button")
        partners_url = url_for('view_partner_list', db_id=db_id)
        showPartners = renderers.render_link('Show Partners', partners_url, class_="button")
        links = [showFunds, showPartners]
    if supplier.paid_in_sterling:
        return links
    transfers_url = url_for('view_foreigntransfer_list', db_id=db_id)
    showForeignTransfers = renderers.render_link('Show Foreign Transfers', transfers_url, class_="button")
    return links + [showForeignTransfers]

def create_transfer(supplier, user):
    transfer = db.ForeignTransfer(parent=supplier.key)
    transfer.creator = user.key
    ref = model.get_next_ref()
    transfer.ref_id = 'FT%04d' % ref
    transfer.put()
    return transfer

def process_transfer_request(supplier, user):
    grant_list = db.Grant.query(db.Grant.state_index == grants.GRANT_READY).fetch()
    if len(grant_list) == 0:
        return None
    transfer = create_transfer(supplier, user)
    for grant in grant_list:
        if getattr(grant, 'transfer', None) is None:
            grant.transfer = transfer.key
            grant.put()
    return transfer

def render_grants_due_list(supplier):
    cutoff_date = datetime.date.today() + datetime.timedelta(21)
    grant_list = db.find_pending_payments(supplier, cutoff_date)
    field_list = (grants.state_field, grants.creator_field, grants.source_field, grants.project_field, grants.amount_field)
    sub_heading = renderers.sub_heading('Grant Payments Due')
    table = readonly_fields.render_table(grant_list, field_list)
    return (sub_heading, table)

def render_purchase_payments_list(supplier):
    advance_list = db.Purchase.query(db.Purchase.supplier == supplier.key).filter(
                         db.Purchase.advance.paid == False).fetch()
    advance_field_list = (purchases.advance_type_field, purchases.po_number_field, purchases.creator_field, grants.source_field, 
                          purchases.advance_amount_field)
    column_headers, advance_grid, advance_url_list = readonly_fields.generate_table_data(advance_list, advance_field_list)
    purchase_list = db.Purchase.query(db.Purchase.supplier == supplier.key).filter(
                         db.Purchase.invoice.paid == False).fetch()
    purchase_field_list = (purchases.invoice_type_field, purchases.po_number_field, purchases.creator_field, grants.source_field,
                           purchases.invoiced_amount_field)
    unused_headers, purchase_grid, purchase_url_list = readonly_fields.generate_table_data(purchase_list, purchase_field_list)
    sub_heading = renderers.sub_heading('Purchase Payments Due')
    table = renderers.render_table(column_headers, advance_grid + purchase_grid,
                            advance_url_list + purchase_url_list)
    return (sub_heading, table)

@app.route('/supplier/<db_id>', methods=['GET', 'POST'])
def view_supplier(db_id):
    supplier = model.lookup_entity(db_id)
    user = views.current_user()
    form = SupplierForm(request.form, obj=supplier)
    buttons = []
    if views.process_edit_button(update_action, form, supplier, user, buttons):
        supplier.put()
        return redirect(request.base_url)
    error = ""
    if not supplier.paid_in_sterling and views.process_action_button(start_transfer, supplier, user, buttons):
        transfer = process_transfer_request(supplier, user)
        if transfer is not None:
            transfer_url = views.url_for_entity(transfer)
            return redirect(transfer_url)
        error = renderers.render_error("No grants are pending - nothing to transfer")
    breadcrumbs = views.create_breadcrumbs_list(supplier)
    links = get_links(supplier)
    fields = (readonly_fields.ReadOnlyField('name'), )
    grid = renderers.render_grid(supplier, fields)
    title = 'Supplier ' + supplier.name
    purchase_payments = render_purchase_payments_list(supplier)
    content = [error, grid, purchase_payments]
    if supplier.receives_grants:
        grant_payments = render_grants_due_list(supplier)
        content.append(grant_payments)
    return views.render_view(title, breadcrumbs, content, links=links, buttons=buttons)
