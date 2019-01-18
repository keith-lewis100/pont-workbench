#_*_ coding: UTF-8 _*_

from flask import url_for
from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import views
from role_types import RoleType

class SupplierForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class SupplierModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Supplier', RoleType.SUPPLIER_ADMIN)

    def create_entity(self, parent):
        return db.Supplier()

    def load_entities(self, parent):
        return db.Supplier.query().fetch()
        
    def title(self, entity):
        return 'Supplier ' + entity.name

supplier_model = SupplierModel()
        
class SupplierListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, supplier_model, SupplierForm)
 
    def get_fields(self, form):
        return (form._fields['name'], )

class SupplierView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, supplier_model, SupplierForm)
        
    def get_fields(self, form):
        return form._fields.values()
                
    def get_links(self, entity):
        funds_url = url_for('view_supplierfund_list', db_id=entity.key.urlsafe())
        showFunds = renderers.render_link('Show Funds', funds_url, class_="button")
        payments_url = url_for('view_paymentsdue_list', db_id=entity.key.urlsafe())
        showPayments = renderers.render_link('Show Payments Due', payments_url, class_="button")
        return [showFunds, showPayments]

def add_rules(app):
    app.add_url_rule('/supplier_list', view_func=SupplierListView.as_view('view_supplier_list'))
    app.add_url_rule('/supplier/<db_id>/', view_func=SupplierView.as_view('view_supplier'))
