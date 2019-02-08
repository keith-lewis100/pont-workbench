#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import db
import model
import renderers
import custom_fields
import views
from role_types import RoleType

class FundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    committee = wtforms.SelectField(choices=model.committee_labels)
    description = wtforms.TextAreaField()
    code = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class FundModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Fund', RoleType.FUND_ADMIN)

    def create_entity(self, parent):
        return db.Fund()

    def load_entities(self, parent):
        return db.Fund.query().fetch()
        
    def title(self, entity):
        return 'Fund ' + entity.name

fund_model = FundModel()

class FundListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, fund_model)
        
    def create_form(self, request_input, entity):
        return FundForm(request_input, obj=entity)

    def get_fields(self, form):
        return (views.ReadOnlyField('name'), views.ReadOnlyField('code'), 
                 views.ReadOnlySelectField('committee', 'Committee', model.committee_labels))

class FundView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, fund_model)
        
    def create_form(self, request_input, entity):
        return FundForm(request_input, obj=entity)

    def get_fields(self, form):
        return map(views.create_form_field, form._fields.keys(), form._fields.values())

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
    app.add_url_rule('/fund_list', view_func=FundListView.as_view('view_fund_list'))
    app.add_url_rule('/fund/<db_id>/', view_func=FundView.as_view('view_fund'))        
