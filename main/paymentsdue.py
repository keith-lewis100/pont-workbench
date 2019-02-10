#_*_ coding: UTF-8 _*_

from flask import url_for
from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import readonly_fields
import views
import grants
import datetime

payments_field_list = [
    grants.state_field,
    readonly_fields.ReadOnlyField('requestor', 'Requestor'),
    readonly_fields.ReadOnlyField('amount', 'Amount'),
    readonly_fields.ReadOnlyField('project_name', 'Project Name'),
    readonly_fields.ReadOnlyField('partner', 'Implementing Partner'),
    readonly_fields.ReadOnlyField('source_fund', 'Source Fund'),
    readonly_fields.ReadOnlyField('dest_fund', 'Destination Fund')
]

class Payment:
    pass

class PaymentsDueModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'PaymentsDue', None)

    def create_entity(self, parent):
        return None

    def load_entities(self, parent):
        cutoff_date = datetime.date.today() + datetime.timedelta(21)
        grant_list = db.find_pending_payments(cutoff_date)
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
        
    def title(self, entity):
        return 'PaymentsDue ' + entity.name

paymentsdue_model = PaymentsDueModel()

class PaymentsDueView(views.ListViewNoCreate):
    def __init__(self):
        views.ListViewNoCreate.__init__(self, paymentsdue_model)
 
    def get_fields(self):
        return payments_field_list

def add_rules(app):
    app.add_url_rule('/paymentsdue/<db_id>', view_func=PaymentsDueView.as_view('view_paymentsdue_list'))
