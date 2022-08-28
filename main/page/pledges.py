#_*_ coding: UTF-8 _*_

from application import app
from flask import request
import wtforms

import db
import data_models
import custom_fields
import properties
import views
from role_types import RoleType

STATE_PENDING = 1
STATE_FULFILLED = 2

state_labels = ['Closed', 'Pending', 'Fulfilled']

def perform_create(model, action_name):
        form = model.get_form(action_name)
        if not form.validate():
            return False
        entity = model.entity
        form.populate_obj(entity)
        ref = data_models.get_next_ref()
        entity.ref_id = 'PL%04d' % ref
        entity.creator = model.user.key
        entity.put()
        model.audit(action_name, "Create performed")
        return True

def perform_fulfilled(model, action_name):
    model.entity.state_index = STATE_FULFILLED
    model.entity.put()
    model.audit(action_name, 'Fulfilled performed')

ACTION_FULFILLED = views.StateAction('fulfilled', 'Fulfilled', RoleType.INCOME_ADMIN,
                                     perform_fulfilled, [STATE_PENDING])
ACTION_BOOKED = views.StateAction('booked', 'Booked', RoleType.FUND_ADMIN,
                                  data_models.Model.perform_close, [STATE_FULFILLED])
ACTION_UPDATE = views.update_action(RoleType.COMMITTEE_ADMIN, [STATE_PENDING])
ACTION_CREATE = views.Action('create', 'New', RoleType.COMMITTEE_ADMIN, perform_create)

state_field = properties.SelectProperty('state_index', 'State', enumerate(state_labels))
ref_id_field = properties.StringProperty('ref_id', 'Reference')
description_field = properties.StringProperty('description')

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class PledgeForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=custom_fields.form_field_widget)
    description = wtforms.TextAreaField()

@app.route('/pledge_list/<db_id>', methods=['GET', 'POST'])
def view_pledge_list(db_id):
    fund = data_models.lookup_entity(db_id)
    new_pledge = db.Pledge(parent=fund.key)
    model = data_models.Model(new_pledge, fund.committee, db.Pledge)
    form = PledgeForm(request.form, obj=new_pledge)
    model.add_form(ACTION_CREATE.name, form)
    property_list = (state_field, ref_id_field, properties.StringProperty('amount'))
    pledge_query = db.Pledge.query(ancestor=fund.key).order(-db.Pledge.state_index,
                                                            db.Pledge.ref_id)
    return views.view_std_entity_list(model, 'Pledge List', ACTION_CREATE, property_list, 
                                      pledge_query, fund, description_field)

@app.route('/pledge/<db_id>', methods=['GET', 'POST'])
def view_pledge(db_id):
    pledge = data_models.lookup_entity(db_id)
    fund = data_models.get_parent(pledge)
    model = data_models.Model(pledge, fund.committee)
    form = PledgeForm(request.form, obj=pledge)
    model.add_form(ACTION_UPDATE.name, form)
    title = 'Pledge ' + pledge.ref_id
    property_list = (ref_id_field, state_field, properties.KeyProperty('creator'),
              properties.StringProperty('amount'), description_field)
    return views.view_std_entity(model, title, property_list,
                                 (ACTION_UPDATE, ACTION_FULFILLED, ACTION_BOOKED))
