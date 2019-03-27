#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import db
import data_models
import renderers
import custom_fields
import properties
import views
from role_types import RoleType

ACTION_UPDATE = views.update_action(RoleType.FUND_ADMIN)
ACTION_CREATE = views.create_action(RoleType.FUND_ADMIN)

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
        return (properties.StringProperty('name'), properties.StringProperty('code'))

class FundView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE, 1)
        
    def title(self, entity):
        return 'Fund ' + entity.name
        
    def create_form(self, request_input, entity):
        return FundForm(request_input, obj=entity)

    def get_fields(self, form):
        return map(properties.create_readonly_field, form._fields.keys(), form._fields.values())

    def get_links(self, entity):
        return [views.render_link(kind, label, entity) for kind, label in [
                    ('Purchase', 'Show Purchase Requests'),
                    ('Grant', 'Show Grants'),
                    ('Pledge', 'Show Pledges'),
                    ('InternalTransfer', 'Show Transfers')]]

def add_rules(app):
    app.add_url_rule('/fund_list/<db_id>', view_func=FundListView.as_view('view_fund_list'))
    app.add_url_rule('/fund/<db_id>/', view_func=FundView.as_view('view_fund'))        
