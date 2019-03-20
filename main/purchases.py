#_*_ coding: UTF-8 _*_

from flask import request, redirect, url_for
from application import app
import wtforms

import db
import model
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

class CheckedAction(model.StateAction):
    def apply_to(self, entity, user=None):
        entity.state_index = PURCHASE_READY
        ref = model.get_next_ref()    
        entity.po_number = 'MB%04d' % ref
        entity.put()

ACTION_CHECKED = CheckedAction('checked', 'Funds Checked', RoleType.FUND_ADMIN, None, [PURCHASE_CHECKING])
ACTION_ORDERED = model.StateAction('ordered', 'Ordered', RoleType.COMMITTEE_ADMIN, PURCHASE_ORDERED, [PURCHASE_READY])
ACTION_INVOICED = model.Action('invoiced', 'Invoiced', RoleType.COMMITTEE_ADMIN)
ACTION_ADVANCE = model.Action('advance', 'Advance Payment', RoleType.COMMITTEE_ADMIN)
ACTION_PAID = model.StateAction('paid', 'Paid', RoleType.PAYMENT_ADMIN, PURCHASE_CLOSED, [PURCHASE_PAYMENT_DUE])
ACTION_CANCEL = model.StateAction('cancel', 'Cancel', RoleType.COMMITTEE_ADMIN, PURCHASE_CLOSED, [PURCHASE_CHECKING])

ACTION_CREATE = model.Action('create', 'New', RoleType.COMMITTEE_ADMIN)
ACTION_UPDATE = model.StateAction('update', 'Edit', RoleType.COMMITTEE_ADMIN, None, [PURCHASE_CHECKING])

ACTION_ADVANCE_PAID = model.Action('advance_paid', 'Paid', RoleType.PAYMENT_ADMIN)

class PurchaseForm(wtforms.Form):
    quote_amount = wtforms.FormField(custom_fields.MoneyForm, widget=custom_fields.form_field_widget)
    supplier = custom_fields.SelectField(coerce=model.create_key, validators=[wtforms.validators.InputRequired()])
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
    fund = model.lookup_entity(db_id)
    user = views.current_user()
    new_purchase = db.Purchase(parent=fund.key)
    form = create_purchase_form(request.form, new_purchase)
    enabled = ACTION_CREATE.is_allowed(fund, user)
    if request.method == 'POST' and form.validate():
        form.populate_obj(new_purchase)
        ACTION_CREATE.apply_to(new_purchase, user)
        ACTION_CREATE.audit(new_purchase, user)
        return redirect(request.base_url)
    
    new_button = custom_fields.render_dialog_button('New', 'm1', form, enabled)
    breadcrumbs = views.create_breadcrumbs(fund)
    purchase_field_list = (readonly_fields.ReadOnlyKeyField('supplier'),
              readonly_fields.ReadOnlyField('quote_amount'), po_number_field, state_field)
    purchase_list = db.Purchase.query(ancestor=fund.key).fetch()
    entity_table = views.render_entity_list(purchase_list, purchase_field_list)
    return views.render_view('Purchase List', breadcrumbs, entity_table, buttons=[new_button])
                
def get_fields(form):
    return [po_number_field, state_field, invoiced_amount_field, invoice_transferred_field, creator_field] + map(readonly_fields.create_readonly_field,
                form._fields.keys(), form._fields.values())

def process_invoiced_button(purchase, user, buttons):
    form = InvoicedAmountForm(request.form, amount=purchase.quote_amount)
    if (request.method == 'POST' and request.form.get('_action') == 'invoiced' 
              and form.validate()):
        purchase.invoice = db.Payment()
        form.populate_obj(purchase.invoice)
        purchase.state_index = PURCHASE_PAYMENT_DUE
        purchase.put()
        ACTION_INVOICED.audit(purchase, user)
        return True
    enabled = (ACTION_INVOICED.is_allowed(purchase, user) and purchase.state_index == PURCHASE_ORDERED 
                  and (purchase.advance is None or purchase.advance.paid))
    button = custom_fields.render_dialog_button(ACTION_INVOICED.label, 'invoiced', form, enabled)
    buttons.append(button)
    return False

def process_advance_button(purchase, user, buttons):
    form = AdvanceAmountForm(request.form)
    if (request.method == 'POST' and request.form.get('_action') == 'advance' 
              and form.validate()):
        purchase.advance = db.Payment()
        form.populate_obj(purchase.advance)
        purchase.put()
        ACTION_ADVANCE.audit(purchase, user)
        return True
    enabled = (ACTION_ADVANCE.is_allowed(purchase, user) and purchase.state_index == PURCHASE_ORDERED
                    and purchase.advance is None)
    button = custom_fields.render_dialog_button(ACTION_ADVANCE.label, 'advance', form, enabled)
    buttons.append(button)
    return False

@app.route('/purchase/<db_id>', methods=['GET', 'POST'])
def view_purchase(db_id):
    purchase = model.lookup_entity(db_id)
    user = views.current_user()
    form = create_purchase_form(request.form, purchase)
    buttons = []
    if views.process_edit_button(ACTION_UPDATE, form, purchase, user, buttons):
        ACTION_UPDATE.apply_to(purchase, user)
        ACTION_UPDATE.audit(purchase, user)
        return redirect(request.base_url)
    for action in [ACTION_CHECKED, ACTION_ORDERED]:
      if views.process_action_button(action, purchase, user, buttons):
        action.apply_to(purchase, user)
        action.audit(purchase, user)
        return redirect(request.base_url)
    if process_invoiced_button(purchase, user, buttons):
      return redirect(request.base_url)
    if process_advance_button(purchase, user, buttons):
      return redirect(request.base_url)
    for action in [ACTION_PAID, ACTION_CANCEL]:
      if views.process_action_button(action, purchase, user, buttons):
        if action is ACTION_PAID:
            purchase.invoice.paid = True
        purchase.put()
        action.audit(purchase, user)
        return redirect(request.base_url)
    breadcrumbs = views.create_breadcrumbs_list(purchase)
    content = views.render_entity(purchase, get_fields(form), 1)
    if purchase.advance is not None:
        sub_heading = renderers.sub_heading('Advance Payment')
        advance_buttons = []
        if views.process_action_button(ACTION_ADVANCE_PAID, purchase, user, advance_buttons):
          purchase.advance.paid = True
          purchase.put()
          ACTION_ADVANCE_PAID.audit(purchase, user)
          return redirect(request.base_url)        
        advance_fields = (advance_amount_field, advance_paid_field, advance_transferred_field)
        advance_grid = views.render_entity(purchase, advance_fields, 1)
        content = (content, sub_heading, advance_buttons, advance_grid)
    history = views.render_entity_history(purchase.key)
    title = 'Purchase ' + purchase.po_number if purchase.po_number is not None else ""
    return views.render_view(title, breadcrumbs, (content, history), buttons=buttons)

