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
import paymentsdue
import grants

class SupplierForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

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
    entity_table = renderers.render_table(supplier_list, views.url_for_entity, *supplier_field_list)
    return views.render_view('Supplier List', breadcrumbs, entity_table, buttons=[new_button])

def get_links(entity):
    db_id = entity.key.urlsafe()
    funds_url = url_for('view_supplierfund_list', db_id=db_id)
    showFunds = renderers.render_link('Show Funds', funds_url, class_="button")
    partners_url = url_for('view_partner_list', db_id=db_id)
    showPartners = renderers.render_link('Show Partners', partners_url, class_="button")
    transfers_url = url_for('view_foreigntransfer_list', db_id=db_id)
    showForeignTransfers = renderers.render_link('Show Foreign Transfers', transfers_url, class_="button")
    return [showFunds, showPartners, showForeignTransfers]

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

def render_paymentsdue_list():
    cutoff_date = datetime.date.today() + datetime.timedelta(21)
    grant_list = db.find_pending_payments(cutoff_date)
    return paymentsdue.render_payments(grant_list)

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
    if views.process_action_button(start_transfer, supplier, user, buttons):
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
    payments = render_paymentsdue_list()
    sub_heading = renderers.sub_heading('Payments Due for ' + supplier.name)
    content = (error, grid, sub_heading, payments)
    return views.render_view(title, breadcrumbs, content, links=links, buttons=buttons)
