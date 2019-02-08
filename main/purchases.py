#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import db
import model
import renderers
import views
import custom_fields
from role_types import RoleType
from projects import project_model

PURCHASE_CHECKING = 1
#states.State('Checking funds') # 1
PURCHASE_READY = 2
#states.State('Ready') # 2
PURCHASE_ORDERED = 3
#states.State('Ordered') # 3
PURCHASE_FULFILLED = 4
#states.State('Fulfilled') # 4
PURCHASE_CLOSED = 5
#states.State('Closed') # 0

state_field = views.StateField('Closed', 'Ready', 'Ordered', 'Fulfilled', 'Closed')

ACTION_CHECKED = model.Action('checked', 'Funds Checked', RoleType.FUND_ADMIN, PURCHASE_READY, [PURCHASE_CHECKING])
ACTION_ORDERED = model.Action('ordered', 'Ordered', RoleType.COMMITTEE_ADMIN, PURCHASE_ORDERED, [PURCHASE_READY])
ACTION_FULFILLED = model.Action('fulfilled', 'Fulfilled', RoleType.COMMITTEE_ADMIN, PURCHASE_FULFILLED, [ACTION_ORDERED])
ACTION_PAID = model.Action('paid', 'Paid', RoleType.COMMITTEE_ADMIN, PURCHASE_CLOSED, [PURCHASE_FULFILLED])
ACTION_CANCEL = model.Action('cancel', 'Cancel', RoleType.COMMITTEE_ADMIN, PURCHASE_CLOSED, [PURCHASE_CHECKING])

class MoneyForm(wtforms.Form):
    currency = wtforms.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=custom_fields.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=50)])

class PurchaseForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=custom_fields.form_field_widget)

class PurchaseModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Purchase', RoleType.COMMITTEE_ADMIN, PURCHASE_CHECKING)

    def create_entity(self, parent):
        return db.Purchase(parent=parent.key)

    def load_entities(self, parent):
        return db.Purchase.query(ancestor=parent.key).fetch()
                        
    def title(self, entity):
        return 'Purchase '

    def perform_state_change(self, entity, action):
        entity.state_index = action.next_state
        if action.next_state == PURCHASE_APPROVED.index:
            ref = model.get_next_ref()    
            entity.po_number = 'MB%04d' % ref
        entity.put()

purchase_model = PurchaseModel()

class PurchaseListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, purchase_model)

    def create_form(self, request_input, entity):
        return PurchaseForm(request_input, obj=entity)

    def get_fields(self, form):
        po_number = views.ReadOnlyField('po_number', 'PO number')
        return (form._fields['amount'], po_number, state_field)

class PurchaseView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, purchase_model, ACTION_CHECKED, ACTION_ORDERED, 
                            ACTION_FULFILLED, ACTION_PAID, ACTION_CANCEL)

    def create_form(self, request_input, entity):
        return PurchaseForm(request_input, obj=entity)
                
    def get_fields(self, form):
        po_number = views.ReadOnlyField('po_number', 'PO number')
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        return map(views.create_form_field, form._fields.keys(), form._fields.values()) + [po_number, state_field, creator]

def add_rules(app):
    app.add_url_rule('/purchase_list/<db_id>', view_func=PurchaseListView.as_view('view_purchase_list'))
    app.add_url_rule('/purchase/<db_id>/', view_func=PurchaseView.as_view('view_purchase'))
