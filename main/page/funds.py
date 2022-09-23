#_*_ coding: UTF-8 _*_

from google.appengine.ext import ndb
from flask import request
import wtforms
import logging

from application import app
import custom_fields
import db
import data_models
import mailer
import properties
import renderers
import views
import urls
from role_types import RoleType

state_labels = ['Closed', 'Open']

name_field = properties.StringProperty('name')
code_field = properties.StringProperty('code')
description_field = properties.StringProperty('description')
state_field = properties.SelectProperty('state_index', 'State', enumerate(state_labels))

def close_fund(model, action_name):
    model.perform_close(action_name)
    fund = model.entity
    users = model.lookup_users_with_role(RoleType.FUND_ADMIN)
    to_addresses = map(lambda u: u.email, users)
    entity_ref = renderers.render_link(fund.name, urls.url_for_entity(fund, external=True))
    content = renderers.render_div('Fund closed ', entity_ref, ' code=%s' % fund.code)
    mailer.send_email('Workbench Fund Closed', content, to_addresses)

ACTION_UPDATE = views.update_action(RoleType.COMMITTEE_ADMIN)
ACTION_CREATE = views.create_action(RoleType.COMMITTEE_ADMIN)
ACTION_CLOSE = views.StateAction('close', 'Close', RoleType.COMMITTEE_ADMIN,
                       close_fund, [1])

class FundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    code = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

@app.route('/fund_list/<db_id>', methods=['GET', 'POST'])
def view_fund_list(db_id):
    committee = data_models.lookup_committee(db_id)
    new_fund = db.Fund(committee = db_id)
    new_fund.key = ndb.Key('Fund', None)
    model = data_models.Model(new_fund, db_id, db.Fund)
    form = FundForm(request.form, new_fund)
    model.add_form(ACTION_CREATE.name, form)   
    property_list = (name_field, code_field)
    fund_query = db.Fund.query(db.Fund.committee == db_id).order(-db.Fund.state_index, db.Fund.name)
    return views.view_std_entity_list(model, 'Fund List', ACTION_CREATE, property_list,
                                      fund_query, parent=committee)

link_pairs = [('Purchase', 'Show Purchase Requests'),
              ('Grant', 'Show Grants'),
              ('Pledge', 'Show Pledges'),
              ('InternalTransfer', 'Show Transfers')]

@app.route('/fund/<db_id>', methods=['GET', 'POST'])
def view_fund(db_id):
    fund = data_models.lookup_entity(db_id)
    model = data_models.Model(fund, fund.committee, db.Fund)
    form = FundForm(request.form, fund)
    model.add_form(ACTION_UPDATE.name, form)   
    property_list = (state_field, name_field, code_field, description_field)
    return views.view_std_entity(model, 'Fund ' + fund.name, property_list, [ACTION_UPDATE, ACTION_CLOSE], 1, link_pairs)
