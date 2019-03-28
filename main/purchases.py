#_*_ coding: UTF-8 _*_

from flask import request, redirect, url_for
import wtforms

from application import app
import db
import data_models
import renderers
import views
import custom_fields
import properties
from role_types import RoleType

PURCHASE_CLOSED = 0
PURCHASE_CHECKING = 1
PURCHASE_READY = 2
PURCHASE_ORDERED = 3
PURCHASE_PAYMENT_DUE = 4

ADVANCE_PAID = 0
ADVANCE_PENDING = 1

state_field = readonly_fields.StateField('Closed', 'Checking', 'Ready', 'Ordered', 'Payment Due')
po_number_field = readonly_fields.ReadOnlyField('po_number', 'PO number')
creator_field = readonly_fields.ReadOnlyKeyField('creator')
invoiced_amount_field = readonly_fields.ReadOnlyField('invoice.amount', 'Invoiced Amount')
invoiced_paid_field = readonly_fields.ReadOnlyField('invoice.paid')
invoice_type_field = readonly_fields.LiteralField("Invoice", "Type")
invoice_transferred_field = readonly_fields.ExchangeCurrencyField('invoice', 'Transferred Amount')

advance_amount_field = readonly_fields.ReadOnlyField('advance.amount')
advance_paid_field = readonly_fields.ReadOnlyField('advance.paid')
advance_type_field = readonly_fields.LiteralField("Advance", "Type")
advance_transferred_field = readonly_fields.ExchangeCurrencyField('advance', 'Transferred Amount')

class PurchaseState:
    CHECKING = 'Checking'
    READY = 'Ready'
    ORDERED = 'Ordered'
    ADVANCE_PENDING = 'Advance Payment Pending'
    PAYMENT_DUE = 'Payment Due'
    CLOSED = 'Closed'

INDEX_CLOSED = 0
INDEX_CHECKING = 1
INDEX_READY = 2
INDEX_ORDERED = 3
state_list = [PurchaseState.CLOSED, PurchaseState.CHECKING, PurchaseState.READY, PurchaseState.ORDERED]

def state_of(purchase):
    state = state_list[purchase.state_index]
    if state == PurchaseState.ORDERED:
        if purchase.advance != None and not purchase.advance.paid:
            return PurchaseState.ADVANCE_PENDING
        if  purchase.invoice != None and not purchase.invoice.paid:
            return PurchaseState.PAYMENT_DUE
    return state

def invoice_amount(entity):
    if entity.invoice is None:
        return ""
    return entity.invoice.amount

def invoice_paid(entity):
    if entity.invoice is None:
        return ""
    return entity.invoice.paid

state_field = properties.StringProperty(state_of, 'State')
po_number_field = properties.StringProperty('po_number', 'PO number')
creator_field = properties.KeyProperty('creator')
invoiced_amount_field = properties.StringProperty(invoice_amount, 'Invoiced Amount')
invoiced_paid_field = properties.StringProperty(invoice_paid, 'paid')
invoice_type_field = properties.StringProperty(lambda e: 'Invoice', 'Type')
invoice_transferred_field = properties.ExchangeCurrencyProperty('invoice', 'Transferred Amount')

advance_amount_field = properties.StringProperty(lambda e: e.advance.amount, 'Amount')
advance_paid_field = properties.StringProperty(lambda e: e.advance.paid, 'Paid')
advance_type_field = properties.StringProperty(lambda e: 'Advance', 'Type')
advance_transferred_field = properties.ExchangeCurrencyProperty('advance', 'Transferred Amount')


class PurchaseModel(data_models.Model):
    def list_entities(self):
        return db.Purchase.query(ancestor = self.parent.key).fetch()

    def perform_checked(self):
        self.entity.state_index = INDEX_READY
        ref = data_models.get_next_ref()
        self.entity.po_number = 'MB%04d' % ref
        self.entity.put()

    def perform_ordered(self):
        self.entity.state_index = INDEX_ORDERED
        self.entity.put()

    def perform_invoiced(self):
        form = self.get_form('invoiced')
        invoice = db.Payment()
        form.populate_obj(advance)
        self.entity.invoice = invoice
        self.entity.put()

    def perform_advance(self):
        form = self.get_form('advance')
        advance = db.Payment()
        form.populate_obj(advance)
        self.entity.advance = advance
        self.entity.put()

    def perform_paid(self):
        self.entity.invoice.paid = True
        self.entity.state_index = INDEX_CLOSED
        self.entity.put()

    def perform_advance_paid(self):
        self.entity.advance.paid = True
        self.entity.put()

    def perform_cancel(self):
        self.entity.state_index = INDEX_CLOSED
        self.entity.put()

    def get_state(self):
        return state_of(self.entity)

ACTION_CHECKED = views.StateAction('checked', 'Funds Checked', RoleType.FUND_ADMIN,
                                   [PurchaseState.CHECKING])
ACTION_ORDERED = views.StateAction('ordered', 'Ordered', RoleType.COMMITTEE_ADMIN,
                                   [PurchaseState.READY])
ACTION_INVOICED = views.StateAction('invoiced', 'Invoiced', RoleType.COMMITTEE_ADMIN,
                               [PurchaseState.ORDERED], True)
ACTION_ADVANCE = views.StateAction('advance', 'Advance Payment', RoleType.COMMITTEE_ADMIN,
                              [PurchaseState.ORDERED], True)
ACTION_PAID = views.StateAction('paid', 'Paid', RoleType.PAYMENT_ADMIN, [PurchaseState.PAYMENT_DUE])
ACTION_CANCEL = views.StateAction('cancel', 'Cancel', RoleType.COMMITTEE_ADMIN,
                                  [PurchaseState.CHECKING])

ACTION_CREATE = views.Action('create', 'New', RoleType.COMMITTEE_ADMIN)
ACTION_UPDATE = views.StateAction('update', 'Edit', RoleType.COMMITTEE_ADMIN, [PurchaseState.CHECKING], True)

ACTION_ADVANCE_PAID = views.StateAction('advance_paid', 'Paid', RoleType.PAYMENT_ADMIN, [PurchaseState.ADVANCE_PENDING])

class PurchaseForm(wtforms.Form):
    quote_amount = wtforms.FormField(custom_fields.MoneyForm, widget=custom_fields.form_field_widget)
    supplier = custom_fields.SelectField(coerce=data_models.create_key, validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

def add_purchase_form(request_data, model, action):
    form = PurchaseForm(request_data, obj=model.entity)
    supplier_list = db.Supplier.query().fetch()
    custom_fields.set_field_choices(form.supplier, supplier_list)
    model.add_form(action.name, form)

class InvoicedAmountForm(wtforms.Form):
    amount = wtforms.FormField(custom_fields.MoneyForm, label='Invoiced Amount', widget=custom_fields.form_field_widget)

class AdvanceAmountForm(wtforms.Form):
    amount = wtforms.FormField(custom_fields.MoneyForm, label='Advance Amount', widget=custom_fields.form_field_widget)

@app.route('/purchase_list/<db_id>', methods=['GET', 'POST'])
def view_purchase_list(db_id):
    fund = data_models.lookup_entity(db_id)
    new_purchase = db.Purchase(parent=fund.key)
    form = create_purchase_form(request.form, new_purchase)
    committee = data_models.get_owning_committee(fund)
    model = data_models.Model(committee)
    model.add_form('create', form)
    if request.method == 'POST' and form.validate():
        form.populate_obj(new_purchase)
        ACTION_CREATE.apply_to(new_purchase, model.user)
        ACTION_CREATE.audit(new_purchase, model.user)
        return redirect(request.base_url)
    
    breadcrumbs = views.create_breadcrumbs(fund)
    purchase_field_list = (readonly_fields.ReadOnlyKeyField('supplier'),
              readonly_fields.ReadOnlyField('quote_amount'), po_number_field, state_field)
    purchase_list = db.Purchase.query(ancestor=fund.key).fetch()
    entity_table = views.render_entity_list(purchase_list, purchase_field_list)
    buttons = views.view_actions([ACTION_CREATE], model, None)
    return views.render_view('Purchase List', breadcrumbs, entity_table, buttons=buttons)
                
def get_fields(form):
    return [po_number_field, state_field, invoiced_amount_field, invoice_transferred_field, creator_field] + map(readonly_fields.create_readonly_field,
                form._fields.keys(), form._fields.values())

def process_invoiced_button(purchase, user):
    if (request.method == 'POST' and request.form.get('_action') == 'invoiced' 
              and form.validate()):
        purchase.invoice = db.Payment()
        form.populate_obj(purchase.invoice)
        purchase.state_index = PURCHASE_PAYMENT_DUE
        purchase.put()
        ACTION_INVOICED.audit(purchase, user)
        return True
    # enabled = (ACTION_INVOICED.is_allowed(model, purchase) and purchase.state_index == PURCHASE_ORDERED 
                  # and (purchase.advance is None or purchase.advance.paid))
    # button = custom_fields.render_dialog_button(ACTION_INVOICED.label, 'invoiced', form, enabled)
    # buttons.append(button)
    return False

def process_advance_button(purchase, user):
    form = AdvanceAmountForm(request.form)
    if (request.method == 'POST' and request.form.get('_action') == 'advance' 
              and form.validate()):
        purchase.advance = db.Payment()
        form.populate_obj(purchase.advance)
        purchase.put()
        ACTION_ADVANCE.audit(purchase, user)
        return True
    # enabled = (ACTION_ADVANCE.is_allowed(purchase, user) and purchase.state_index == PURCHASE_ORDERED
                    # and purchase.advance is None)
    # button = custom_fields.render_dialog_button(ACTION_ADVANCE.label, 'advance', form, enabled)
    # buttons.append(button)
    return False

@app.route('/purchase/<db_id>', methods=['GET', 'POST'])
def view_purchase(db_id):
    purchase = data_models.lookup_entity(db_id)
    form = create_purchase_form(request.form, purchase)
    committee = data_models.get_owning_committee(purchase)
    model = data_models.Model(committee)
    model.add_form('update', form)
    invoice_form = InvoicedAmountForm(request.form, amount=purchase.quote_amount)
    model.add_form(ACTION_ORDERED.name, invoice_form)
    if views.process_edit_button(ACTION_UPDATE, form, purchase):
        return redirect(request.base_url)
    for action in [ACTION_CHECKED, ACTION_ORDERED]:
      if views.process_action_button(action, model, purchase):
        action.apply_to(purchase, model.user)
        action.audit(purchase, model.user)
        return redirect(request.base_url)
    if process_invoiced_button(purchase, model.user):
      return redirect(request.base_url)
    if process_advance_button(purchase, model.user):
      return redirect(request.base_url)
    for action in [ACTION_PAID, ACTION_CANCEL]:
      if views.process_action_button(action, model, purchase):
        if action is ACTION_PAID:
            purchase.invoice.paid = True
        purchase.put()
        action.audit(purchase, model.user)
=======
    fund = data_models.lookup_entity(db_id, 'Fund')
    new_purchase = db.Purchase(parent=fund.key)
    model = PurchaseModel(None, fund)
    add_purchase_form(request.form, model, ACTION_CREATE)
    property_list = (properties.KeyProperty('supplier'), properties.StringProperty('quote_amount'),
                     po_number_field, state_field)
    return views.view_entity_list(model, 'Purchase List', property_list, ACTION_CREATE)

def get_fields(model):
    form = model.get_form(ACTION_UPDATE.name)
    return [po_number_field, state_field, invoiced_amount_field, invoice_transferred_field, creator_field] + map(properties.create_readonly_field,
                form._fields.keys(), form._fields.values())

def load_purchase_model(db_id, request_data):
    purchase = data_models.lookup_entity(db_id, 'Purchase')
    model = PurchaseModel(purchase)
    add_purchase_form(request_data, model, ACTION_UPDATE)
    invoice_form = InvoicedAmountForm(request_data)
    model.add_form(ACTION_INVOICED.name, invoice_form)
    advance_form = AdvanceAmountForm(request_data)
    model.add_form(ACTION_ADVANCE.name, advance_form)
    return model
    
@app.route('/purchase/<db_id>', methods=['GET', 'POST'])
def view_purchase(db_id):
    model = load_purchase_model(db_id, request.form)
    if request.method == 'POST'and views.handle_post(model, action_list):
        return redirect(request.base_url)
    purchase = model.entity
    breadcrumbs = views.create_breadcrumbs_list(purchase)
    content = views.render_entity(purchase, get_fields(model), 1)
    if purchase.advance is not None:
        sub_heading = renderers.sub_heading('Advance Payment')
        advance_button = ACTION_ADVANCE_PAID.render(model)
        advance_fields = (advance_amount_field, advance_paid_field, advance_transferred_field)
        advance_grid = views.render_entity(purchase, advance_fields)
        content = (content, sub_heading, [advance_button], advance_grid)
    history = views.render_entity_history(purchase.key)
    title = 'Purchase ' + purchase.po_number if purchase.po_number is not None else ""
    action_list = [ACTION_UPDATE, ACTION_CHECKED, ACTION_ORDERED, ACTION_ADVANCE, ACTION_PAID, ACTION_CANCEL]
    buttons = views.view_actions(action_list, model)
    return views.render_view(title, breadcrumbs, (content, history), buttons=buttons)
