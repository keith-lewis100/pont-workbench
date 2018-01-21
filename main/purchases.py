#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import views
import custom_fields
import states

PURCHASE_AUTHORISING = states.State(0, 'Authorising', ('state-change', 1), ('state-change', 5), ('update',))
PURCHASE_APPROVING = states.State(1, 'Approving', ('state-change', 2), ('state-change', 5), ('update',))
PURCHASE_APPROVED = states.State(2, 'Approved', ('state-change', 3), ('state-change', 5))
PURCHASE_ORDERED = states.State(3, 'Ordered', ('state-change', 4))
PURCHASE_FULFILLED = states.State(4, 'Fulfilled', ('state-change', 5))
PURCHASE_CLOSED = states.State(5, 'Closed')

purchaseStates = [PURCHASE_AUTHORISING, PURCHASE_APPROVING, PURCHASE_APPROVED, PURCHASE_ORDERED,
                  PURCHASE_FULFILLED, PURCHASE_CLOSED]

class MoneyForm(wtforms.Form):
    currency = custom_fields.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=50)])

class PurchaseForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)
    
class Purchase(views.EntityType):
    def __init__(self):
        self.name = 'Purchase'
        self.formClass = PurchaseForm

    def get_state(self, index):
        return purchaseStates[index]
        
    def create_entity(self, parent):
        return model.create_purchase(parent)

    def load_entities(self, parent):
        return model.list_purchases(parent)
                        
    def title(self, entity):
        return 'Purchase'

class PurchaseListView(views.ListView):
    def __init__(self):
        self.entityType = Purchase()

    def get_fields(self, form):
        po_number = views.ReadOnlyField('po_number', 'PO number')
        state = views.StateField(purchaseStates)
        return (form._fields['amount'], po_number, state)

class PurchaseView(views.EntityView):
    def __init__(self):
        self.entityType = Purchase()
        self.actions = [(2, 'Approve'), (3, 'Ordered'), (4, 'Fulfilled'), (5, 'Close')]
        
    def get_fields(self, form):
        po_number = views.ReadOnlyField('po_number', 'PO number')
        state = views.StateField(purchaseStates)
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        return form._fields.values() + [po_number, state, creator]

    def get_links(self, entity):
        return []

def add_rules(app):
    app.add_url_rule('/purchase_list/<db_id>', view_func=PurchaseListView.as_view('view_purchase_list'))
    app.add_url_rule('/purchase/<db_id>/', view_func=PurchaseView.as_view('view_purchase'))
    app.add_url_rule('/purchase/<db_id>/menu', view_func=views.MenuView.as_view('handle_purchase_menu'))
