#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views

class SupplierForm(renderers.EntityRenderer):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class SupplierListView(views.ListView):
    def __init__(self):
        self.kind = 'Suppliers'
        self.formClass = SupplierForm
        
    def create_entity(self):
        return model.create_supplier()

    def load_entities(self):
        return model.list_suppliers()

class SupplierView(views.EntityView):
    def __init__(self):
        self.kind = 'Supplier'
        self.formClass = SupplierForm
        
    def lookup_entity(self, org_id):
        return  model.lookup_entity(('Supplier', org_id))
        
    def get_menu(self):
        return []


