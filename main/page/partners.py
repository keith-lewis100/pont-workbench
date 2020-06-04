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

class PartnerForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

@app.route('/partner_list/<db_id>', methods=['GET', 'POST'])
def view_partner_list(db_id):
    supplier = data_models.lookup_entity(db_id)
    new_partner = db.Partner(parent=supplier.key)
    model = data_models.Model(new_partner, None, db.Partner)
    form = PartnerForm(request.form, obj=new_partner)
    model.add_form(ACTION_CREATE.name, form)
    partner_query = db.Partner.query(ancestor=supplier.key).order(db.Partner.name)
    return views.view_std_entity_list(model, 'Partner List', ACTION_CREATE, (name_field, ),
                                      partner_query, supplier)

@app.route('/partner/<db_id>', methods=['GET', 'POST'])
def view_partner(db_id):
    partner = data_models.lookup_entity(db_id)
    supplier = data_models.get_parent(partner)
    model = data_models.Model(partner, None, db.Partner)
    form = PartnerForm(request.form, obj=partner)
    model.add_form(ACTION_UPDATE.name, form)
    return views.view_std_entity(model, 'Partner ' + partner.name, (name_field, ), (ACTION_UPDATE, ))    
