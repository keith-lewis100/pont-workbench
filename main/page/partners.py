#_*_ coding: UTF-8 _*_

import wtforms

import db
import properties
import views
from role_types import RoleType

ACTION_UPDATE = views.update_action(RoleType.SUPPLIER_ADMIN)
ACTION_CREATE = views.create_action(RoleType.SUPPLIER_ADMIN)

class PartnerForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class PartnerListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'Partner', ACTION_CREATE)

    def get_entity_query(self, parent):
        return db.Partner.query(ancestor=parent.key).order(db.Partner.name)

    def create_entity(self, parent):
        return db.Partner(parent=parent.key)
 
    def create_form(self, request_input, entity):
        return PartnerForm(request_input, obj=entity)

    def get_fields(self, form):
        return (properties.StringProperty('name'), )

class PartnerView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE)
        
    def title(self, entity):
        return 'Partner ' + entity.name
 
    def create_form(self, request_input, entity):
        return PartnerForm(request_input, obj=entity)
        
    def get_fields(self, form):
        return (properties.StringProperty('name'), )

def add_rules(app):
    app.add_url_rule('/partner_list/<db_id>', view_func=PartnerListView.as_view('view_partner_list'))
    app.add_url_rule('/partner/<db_id>/', view_func=PartnerView.as_view('view_partner'))
