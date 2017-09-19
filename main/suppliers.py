#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views

class SupplierForm(wtforms.Form):
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
        self.actions = []
        
    def get_fields(self, form):
        return form._fields.values()
        
    def title(self, entity):
        return entity.name
                
    def get_links(self, entity):
        return ""

def add_rules(app):
    app.add_url_rule('/suppliers', view_func=SupplierListView.as_view('view_supplier_list'))
    app.add_url_rule('/supplier/<db_id>/', view_func=SupplierView.as_view('view_supplier'))
