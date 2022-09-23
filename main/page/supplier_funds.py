#_*_ coding: UTF-8 _*_

from flask import request
from application import app
import wtforms

import custom_fields
import data_models
import db
import properties
import views
from role_types import RoleType

name_field = properties.StringProperty('name')

ACTION_UPDATE = views.update_action(RoleType.SUPPLIER_ADMIN)
ACTION_CREATE = views.create_action(RoleType.SUPPLIER_ADMIN)

class SupplierFundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    partner_required = wtforms.BooleanField('Project Partner Required')
    description = wtforms.TextAreaField()

@app.route('/supplierfund_list/<db_id>', methods=['GET', 'POST'])
def view_supplierfund_list(db_id):
    supplier = data_models.lookup_entity(db_id)
    new_fund = db.SupplierFund(parent=supplier.key)
    model = data_models.Model(new_fund, None, db.SupplierFund)
    form = SupplierFundForm(request.form, obj=new_fund)
    model.add_form(ACTION_CREATE.name, form)
    fund_query = db.SupplierFund.query(ancestor=supplier.key).order(db.SupplierFund.name)
    return views.view_std_entity_list(model, 'SupplierFund List', ACTION_CREATE, (name_field, ),
                                      fund_query, parent=supplier)

@app.route('/supplierfund/<db_id>', methods=['GET', 'POST'])
def view_supplierfund(db_id):
    fund = data_models.lookup_entity(db_id)
    supplier = data_models.get_parent(fund)
    model = data_models.Model(fund, None, db.SupplierFund)
    if request.form:
      form = SupplierFundForm(request.form)
    else:
      form = SupplierFundForm(obj=fund)
    model.add_form(ACTION_UPDATE.name, form)
    property_list = map(properties.create_readonly_field, form._fields.keys(),
                        form._fields.values())
    return views.view_std_entity(model, 'SupplierFund ' + fund.name, property_list,
                                 (ACTION_UPDATE, ), num_wide=1)
