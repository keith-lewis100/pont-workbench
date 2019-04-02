#_*_ coding: UTF-8 _*_

from flask import request
import wtforms

from application import app
import db
import data_models
import properties
import views
from role_types import RoleType

name_field = properties.StringProperty('name')
code_field = properties.StringProperty('code')
description_field = properties.StringProperty('description')

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
    model = data_models.Model(new_fund, committee.id)
    form = FundForm(request.form, new_fund)
    model.add_form(ACTION_CREATE.name, form)   
    property_list = (name_field, code_field)
    fund_list = db.Fund.query(db.Fund.committee == committee.id).fetch()
    entity_table = views.render_entity_list(fund_list, property_list)
    new_button = ACTION_CREATE.render(model)
    breadcrumbs = views.create_breadcrumbs(fund)
    return views.render_view('Fund List', breadcrumbs, entity_table, buttons=[new_button])

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
    property_list = (name_field, code_field, description_field)
    return views.view_std_entity(model, 'Fund ' + fund.name, property_list, [ACTION_UPDATE], 1, get_links(fund))
