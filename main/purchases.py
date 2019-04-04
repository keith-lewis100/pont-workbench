#_*_ coding: UTF-8 _*_

from flask import request, redirect, url_for
from application import app
import wtforms

import db
import data_models
import renderers
import views
import custom_fields
import readonly_fields
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

class CheckedAction(data_models.StateAction):
    def apply_to(self, entity, user=None):
        entity.state_index = PURCHASE_READY
        ref = data_models.get_next_ref()    
        entity.po_number = 'MB%04d' % ref
        entity.put()

ACTION_CHECKED = CheckedAction('checked', 'Funds Checked', RoleType.FUND_ADMIN, None, [PURCHASE_CHECKING])
ACTION_ORDERED = data_models.StateAction('ordered', 'Ordered', RoleType.COMMITTEE_ADMIN, PURCHASE_ORDERED, [PURCHASE_READY])
ACTION_INVOICED = data_models.Action('invoiced', 'Invoiced', RoleType.COMMITTEE_ADMIN)
ACTION_ADVANCE = data_models.Action('advance', 'Advance Payment', RoleType.COMMITTEE_ADMIN)
ACTION_PAID = data_models.StateAction('paid', 'Paid', RoleType.PAYMENT_ADMIN, PURCHASE_CLOSED, [PURCHASE_PAYMENT_DUE])
ACTION_CANCEL = data_models.StateAction('cancel', 'Cancel', RoleType.COMMITTEE_ADMIN, PURCHASE_CLOSED, [PURCHASE_CHECKING])

ACTION_CREATE = data_models.Action('create', 'New', RoleType.COMMITTEE_ADMIN)
ACTION_UPDATE = data_models.StateAction('update', 'Edit', RoleType.COMMITTEE_ADMIN, None, [PURCHASE_CHECKING])

ACTION_ADVANCE_PAID = data_models.Action('advance_paid', 'Paid', RoleType.PAYMENT_ADMIN)

class PurchaseForm(wtforms.Form):
    quote_amount = wtforms.FormField(custom_fields.MoneyForm, widget=custom_fields.form_field_widget)
    supplier = custom_fields.SelectField(coerce=data_models.create_key, validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

def create_purchase_form(request_input, entity):
    form = PurchaseForm(request_input, obj=entity)
    supplier_list = db.Supplier.query().fetch()
    custom_fields.set_field_choices(form._fields['supplier'], supplier_list)
    return form

class InvoicedAmountForm(wtforms.Form):
    amount = wtforms.FormField(custom_fields.MoneyForm, label='Invoiced Amount', widget=custom_fields.form_field_widget)

class AdvanceAmountForm(wtforms.Form):
    amount = wtforms.FormField(custom_fields.MoneyForm, label='Advance Amount', widget=custom_fields.form_field_widget)

@app.route('/purchase_list/<db_id>', methods=['GET', 'POST'])
def view_purchase_list(db_id):
    fund = data_models.lookup_entity(db_id)
    new_purchase = db.Purchase(parent=fund.key)
    form = create_purchase_form(request.form, new_purchase)
    model = data_models.Model(new_purchase, fund.committee)
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
    buttons = views.view_actions([ACTION_CREATE], model)
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
    model = data_models.Model(purchase, committee)
    model.add_form('update', form)
    invoice_form = InvoicedAmountForm(request.form, amount=purchase.quote_amount)
    model.add_form(ACTION_ORDERED.name, invoice_form)
    if views.process_edit_button(ACTION_UPDATE, model, form):
        return redirect(request.base_url)
    for action in [ACTION_CHECKED, ACTION_ORDERED]:
      if views.process_action_button(action, model):
        action.apply_to(purchase, model.user)
        action.audit(purchase, model.user)
        return redirect(request.base_url)
    if process_invoiced_button(purchase, model.user):
      return redirect(request.base_url)
    if process_advance_button(purchase, model.user):
      return redirect(request.base_url)
    for action in [ACTION_PAID, ACTION_CANCEL]:
      if views.process_action_button(action, model):
        if action is ACTION_PAID:
            purchase.invoice.paid = True
        purchase.put()
        action.audit(purchase, model.user)
        return redirect(request.base_url)
    breadcrumbs = views.create_breadcrumbs_list(purchase)
    content = views.render_entity(purchase, get_fields(form), 1)
    if purchase.advance is not None:
        sub_heading = renderers.sub_heading('Advance Payment')
        advance_buttons = []
        if views.process_action_button(ACTION_ADVANCE_PAID, model):
          purchase.advance.paid = True
          purchase.put()
          ACTION_ADVANCE_PAID.audit(purchase, model.user)
          return redirect(request.base_url)
        advance_buttons = [ACTION_ADVANCE_PAID.render(model, purchase)]
        advance_fields = (advance_amount_field, advance_paid_field, advance_transferred_field)
        advance_grid = views.render_entity(purchase, advance_fields, 1)
        content = (content, sub_heading, advance_buttons, advance_grid)
    history = views.render_entity_history(purchase.key)
    title = 'Purchase ' + purchase.po_number if purchase.po_number is not None else ""
    action_list = [ACTION_UPDATE, ACTION_CHECKED, ACTION_ORDERED, ACTION_ADVANCE, ACTION_PAID, ACTION_CANCEL]
    buttons = views.view_actions(action_list, model, purchase)
    return views.render_view(title, breadcrumbs, (content, history), buttons=buttons)

