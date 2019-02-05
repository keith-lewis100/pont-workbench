#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import db
import model
import renderers
import custom_fields
import views
from role_types import RoleType

class PartnerForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class PartnerModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Partner', RoleType.SUPPLIER_ADMIN)

    def create_entity(self, parent):
        return db.Partner(parent=parent.key)

    def load_entities(self, parent):
        return db.Partner.query(ancestor=parent.key).fetch()
        
    def title(self, entity):
        return 'Partner ' + entity.name

partner_model = PartnerModel()

class PartnerListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, partner_model)
 
    def create_form(self, request_input, entity):
        return PartnerForm(request_input, obj=entity)

    def get_fields(self, form):
        return (form._fields['name'], )

class PartnerView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, partner_model)
 
    def create_form(self, request_input, entity):
        return PartnerForm(request_input, obj=entity)
        
    def get_fields(self, form):
        return form._fields.values()

def add_rules(app):
    app.add_url_rule('/partner_list/<db_id>', view_func=PartnerListView.as_view('view_partner_list'))
    app.add_url_rule('/partner/<db_id>/', view_func=PartnerView.as_view('view_partner'))
