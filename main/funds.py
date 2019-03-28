#_*_ coding: UTF-8 _*_

from flask import request
import wtforms

from application import app
import db
import data_models
import properties
import views
from role_types import RoleType

ACTION_UPDATE = views.update_action(RoleType.FUND_ADMIN)
ACTION_CREATE = views.create_action(RoleType.FUND_ADMIN)

class FundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    code = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

@app.route('/fund_list/<db_id>', methods=['GET', 'POST'])
def view_fund_list(db_id):
    committee = data_models.lookup_committee(db_id)
    new_fund = db.Fund(committee = committee.id)
    model = FundModel(None, committee)
    form = FundForm(request.form, new_fund)
    model.add_form(ACTION_CREATE.name, form)   
    property_list = (properties.StringProperty('name'), properties.StringProperty('code'))
    return views.view_entity_list(model, 'Fund List', property_list, ACTION_CREATE)

def get_links(fund):
    return [views.render_link(kind, label, fund) for kind, label in [
                ('Purchase', 'Show Purchase Requests'),
                ('Grant', 'Show Grants'),
                ('Pledge', 'Show Pledges'),
                ('InternalTransfer', 'Show Transfers')]]

@app.route('/fund/<db_id>', methods=['GET', 'POST'])
def view_fund(db_id):
    fund = data_models.lookup_entity(db_id, 'Fund')
    model = FundModel(fund)
    form = FundForm(request.form, fund)
    model.add_form(ACTION_UPDATE.name, form)   
    property_list = map(properties.create_readonly_field, form._fields.keys(), form._fields.values())
    return views.view_std_entity(model, 'Fund ' + fund.name, property_list, [ACTION_UPDATE], 1, get_links(fund))
