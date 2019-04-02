#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import db
import data_models
import renderers
import custom_fields
import readonly_fields
import views
from role_types import RoleType

ACTION_UPDATE = data_models.Action('update', 'Edit', RoleType.FUND_ADMIN)
ACTION_CREATE = data_models.CreateAction(RoleType.FUND_ADMIN)

class FundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    code = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

class FundListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'Fund', ACTION_CREATE)

    def load_entities(self, committee):
        return db.Fund.query(db.Fund.committee == committee.id).fetch()

    def create_entity(self, committee):
        return db.Fund(committee = committee.id)

    def create_form(self, request_input, entity):
        return FundForm(request_input, obj=entity)

    def get_fields(self, form):
        return (readonly_fields.ReadOnlyField('name'), readonly_fields.ReadOnlyField('code'))

class FundView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE, 1)
        
    def title(self, entity):
        return 'Fund ' + entity.name
        
    def create_form(self, request_input, entity):
        return FundForm(request_input, obj=entity)

    def get_fields(self, form):
        return map(readonly_fields.create_readonly_field, form._fields.keys(), form._fields.values())

    def get_links(self, entity):
        purchases_url = url_for('view_purchase_list', db_id=entity.key.urlsafe())
        showPurchases = renderers.render_link('Show Purchase Requests', purchases_url, class_="button")
        grants_url = url_for('view_grant_list', db_id=entity.key.urlsafe())
        showGrants = renderers.render_link('Show Grants', grants_url, class_="button")
        pledges_url = url_for('view_pledge_list', db_id=entity.key.urlsafe())
        showPledges = renderers.render_link('Show Pledges', pledges_url, class_="button")
        transfers_url = url_for('view_internaltransfer_list', db_id=entity.key.urlsafe())
        showTransfers = renderers.render_link('Show Transfers', transfers_url, class_="button")        
        return [showPurchases, showGrants, showPledges, showTransfers]

def add_rules(app):
    app.add_url_rule('/fund_list/<db_id>', view_func=FundListView.as_view('view_fund_list'))
    app.add_url_rule('/fund/<db_id>/', view_func=FundView.as_view('view_fund'))        
