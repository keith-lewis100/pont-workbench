#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import db
import model
import renderers
import views
import custom_fields
import states
from role_types import RoleType
from projects import project_model

PURCHASE_CHECKING = states.State('Checking funds') # 1
PURCHASE_READY = states.State('Ready') # 2
PURCHASE_ORDERED = states.State('Ordered') # 3
PURCHASE_FULFILLED = states.State('Fulfilled') # 4
PURCHASE_CLOSED = states.State('Closed') # 0

state_map = {
    'checked': 2,
    'ordered': 3
}

purchaseStates = [PURCHASE_CLOSED, PURCHASE_CHECKING, PURCHASE_READY, PURCHASE_ORDERED,
                  PURCHASE_FULFILLED]

class MoneyForm(wtforms.Form):
    currency = custom_fields.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=50)])

class PurchaseForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)

class PurchaseModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Purchase', RoleType.COMMITTEE_ADMIN, project_model, purchaseStates)

    def create_entity(self, parent):
        return db.Purchase(parent=parent.key)

    def load_entities(self, parent):
        return db.Purchase.query(ancestor=parent.key).fetch()
                        
    def title(self, entity):
        return 'Purchase ' + str(entity.key.id())

    def perform_state_change(self, entity, state_index):
        entity.state_index = state_index
        if state_index == PURCHASE_APPROVED.index:
            ref = model.get_next_ref()    
            entity.po_number = 'MB%04d' % ref
        entity.put()

purchase_model = PurchaseModel()

class PurchaseListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, purchase_model, PurchaseForm)

    def get_fields(self, form):
        id = views.IdField()
        po_number = views.ReadOnlyField('po_number', 'PO number')
        state = views.StateField(purchaseStates)
        return (id, form._fields['amount'], po_number, state)

class PurchaseView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, purchase_model, PurchaseForm, ('checked', 'Funds Checked'), 
               ('ordered', 'Ordered'), ('fulfilled', 'Fulfilled'), ('paid', 'Paid'))
                
    def get_fields(self, form):
        po_number = views.ReadOnlyField('po_number', 'PO number')
        state = views.StateField(purchaseStates)
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        return form._fields.values() + [po_number, state, creator]

def add_rules(app):
    app.add_url_rule('/purchase_list/<db_id>', view_func=PurchaseListView.as_view('view_purchase_list'))
    app.add_url_rule('/purchase/<db_id>/', view_func=PurchaseView.as_view('view_purchase'))
    app.add_url_rule('/purchase/<db_id>/menu', view_func=views.MenuView.as_view('handle_purchase_menu', purchase_model))
