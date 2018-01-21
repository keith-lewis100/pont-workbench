#_*_ coding: UTF-8 _*_

from flask import url_for
from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views

class SupplierForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class Supplier(views.EntityType):
    def __init__(self):
        self.name = 'Supplier'
        self.formClass = SupplierForm

    def get_state(self, index):
        return None
        
    def create_entity(self, parent):
        return model.create_supplier()

    def load_entities(self, parent):
        return model.list_suppliers()
        
    def title(self, entity):
        return 'Supplier ' + entity.name

class SupplierListView(views.ListView):
    def __init__(self):
        self.entityType = Supplier()
 
    def get_fields(self, form):
        return (form._fields['name'], )

class SupplierView(views.EntityView):
    def __init__(self):
        self.entityType = Supplier()
        self.actions = []
        
    def get_fields(self, form):
        return form._fields.values()
                
    def get_links(self, entity):
        funds_url = url_for('view_supplier_fund_list', db_id=entity.key.urlsafe())
        showFunds = renderers.render_link('Show Funds', funds_url, class_="button")
        return [showFunds]

def add_rules(app):
    app.add_url_rule('/supplier_list', view_func=SupplierListView.as_view('view_supplier_list'))
    app.add_url_rule('/supplier/<db_id>/', view_func=SupplierView.as_view('view_supplier'))
