#_*_ coding: UTF-8 _*_

from flask import render_template, request, redirect
from application import app

import db
import model
import renderers
import readonly_fields
import views
import datetime
import grants
from role_types import RoleType

payments_field_list = [
    grants.state_field,
    readonly_fields.ReadOnlyField('requestor', 'Requestor'),
    readonly_fields.ReadOnlyField('amount', 'Amount'),
    readonly_fields.ReadOnlyField('project_name', 'Project Name'),
    readonly_fields.ReadOnlyField('partner', 'Implementing Partner'),
    readonly_fields.ReadOnlyField('source_fund', 'Source Fund'),
    readonly_fields.ReadOnlyField('dest_fund', 'Destination Fund')
]

def create_transfer(supplier, user):
    transfer = db.ForeignTransfer(parent=supplier.key)
    transfer.creator = user.key
    ref = model.get_next_ref()
    transfer.ref_id = 'FT%04d' % ref
    transfer.put()
    return transfer

class StartTransferAction(model.Action):
    def __init__(self):
        super(StartTransferAction, self).__init__('startTransfer', 'Request Foreign Transfer', 
                 RoleType.PAYMENT_ADMIN)

    def apply_to(self, supplier, user):
        transfer = create_transfer(supplier, user)
        grant_list = db.Grant.query(db.Grant.state_index == grants.GRANT_READY).fetch()
        for grant in grant_list:
            grant.transfer = transfer.key
            grant.put()

start_transfer = StartTransferAction()

class Payment:
    pass

def load_payments(grant_list):
    payments_list = []
    for grant in grant_list:
        p = Payment()
        p.key = grant.key
        p.state_index = grant.state_index
        p.requestor = grant.creator.get().name
        p.amount = grant.amount
        project = grant.project.get()
        p.project_name = project.name
        p.partner = None
        if (project.partner != None):
          p.partner = project.partner.get().name
        p.source_fund = grant.key.parent().get().code
        p.dest_fund = grant.project.parent().get().name
        payments_list.append(p)
    return payments_list

@app.route('/paymentsdue/<db_id>', methods=['GET', 'POST'])
def view_paymentsdue_list(db_id):
    supplier = model.lookup_entity(db_id)
    user = views.current_user()
    buttons = []
    transfer_url = views.url_for_list('ForeignTransfer', supplier)
    if views.process_action_button(start_transfer, supplier, user, buttons):
        return redirect(transfer_url)
    breadcrumbs = views.create_breadcrumbs(supplier)
    cutoff_date = datetime.date.today() + datetime.timedelta(21)
    grant_list = db.find_pending_payments(cutoff_date)
    entity_list = load_payments(grant_list)
    entity_table = renderers.render_table(entity_list, views.url_for_entity, *payments_field_list)
    return views.render_view('Payments Due List', breadcrumbs, entity_table, buttons=buttons)
