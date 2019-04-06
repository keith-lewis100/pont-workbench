#_*_ coding: UTF-8 _*_

from flask import request, redirect, render_template
import wtforms

from application import app
import db
import data_models
import renderers
import views
import custom_fields
import properties
from role_types import RoleType

STATE_CHECKING = 1
STATE_READY = 2
STATE_ORDERED = 3
STATE_ADVANCE_PENDING = 4
STATE_PAYMENT_DUE = 5

state_labels = ['Closed', 'Checking', 'Ready', 'Ordered', 'Advance Payment Pending', 'Payment Due']

def state_of(purchase):
    state = purchase.state_index
    if state == STATE_ORDERED:
        if purchase.advance != None and not purchase.advance.paid:
            return STATE_ADVANCE_PENDING
        if  purchase.invoice != None and not purchase.invoice.paid:
            return STATE_PAYMENT_DUE
    return state

supplier_field = properties.KeyProperty('supplier')
quote_amount_field = properties.StringProperty('quote_amount')
description_field = properties.StringProperty('description')
state_field = properties.SelectProperty(state_of, 'State', enumerate(state_labels))
po_number_field = properties.StringProperty('po_number', 'PO number')
creator_field = properties.KeyProperty('creator')

invoiced_amount_field = properties.StringProperty(lambda e: e.advance.amount, 'Invoiced Amount')
invoiced_paid_field = properties.StringProperty(lambda e: e.advance.paid, 'paid')
invoice_type_field = properties.StringProperty(lambda e: 'Invoice', 'Type')
invoice_transferred_field = properties.StringProperty(lambda e: data_models.calculate_transferred_amount(e.invoice), 
                                    'Transferred Amount')

def advance_transferred_amount(purchase):
    return data_models.calculate_transferred_amount(payment)
advance_amount_field = properties.StringProperty(lambda e: e.advance.amount, 'Amount')
advance_paid_field = properties.StringProperty(lambda e: e.advance.paid, 'Paid')
advance_type_field = properties.StringProperty(lambda e: 'Advance', 'Type')
advance_transferred_field = properties.StringProperty(lambda e: data_models.calculate_transferred_amount(e.advance), 
                                    'Transferred Amount')


class PurchaseModel(data_models.Model):
    def perform_checked(self, action_name):
        entity = self.entity
        entity.state_index = STATE_READY
        ref = data_models.get_next_ref()
        entity.po_number = 'MB%04d' % ref
        entity.put()
        self.audit(action_name, "Check performed")
        return True


    def perform_ordered(self, action_name):
        self.entity.state_index = STATE_ORDERED
        self.entity.put()
        self.audit(action_name, "Ordered performed")
        return True

    def perform_invoiced(self, action_name):
        form = self.get_form('invoiced')
        if not form.validate():
            return False
        invoice = db.Payment()
        form.populate_obj(invoice)
        self.entity.invoice = invoice
        self.entity.put()
        self.audit(action_name, "Invoiced amount=%s" % invoice.amount)
        return True

    def perform_advance(self, action_name):
        form = self.get_form('advance')
        if not form.validate():
            return False
        advance = db.Payment()
        form.populate_obj(advance)
        self.entity.advance = advance
        self.entity.put()
        self.audit(action_name, "Advanced amount=%s" % advance.amount)
        return True

    def perform_paid(self, action_name):
        self.entity.invoice.paid = True
        self.entity.state_index = data_models.STATE_CLOSED
        self.entity.put()
        self.audit(action_name, "Paid performed")
        return True

    def perform_advance_paid(self, action_name):
        self.entity.advance.paid = True
        self.entity.put()
        self.audit(action_name, "Advance paid performed")
        return True

    def get_state(self):
        return state_of(self.entity)

ACTION_CHECKED = views.StateAction('checked', 'Funds Checked', RoleType.FUND_ADMIN,
                                   PurchaseModel.perform_checked, [STATE_CHECKING])
ACTION_ORDERED = views.StateAction('ordered', 'Ordered', RoleType.COMMITTEE_ADMIN,
                                   PurchaseModel.perform_ordered, [STATE_READY])
ACTION_INVOICED = views.StateAction('invoiced', 'Invoiced', RoleType.COMMITTEE_ADMIN,
                               PurchaseModel.perform_invoiced, [STATE_ORDERED])
ACTION_ADVANCE = views.StateAction('advance', 'Advance Payment', RoleType.COMMITTEE_ADMIN,
                              PurchaseModel.perform_advance, [STATE_ORDERED])
ACTION_PAID = views.StateAction('paid', 'Paid', RoleType.PAYMENT_ADMIN,
                                PurchaseModel.perform_close, [STATE_PAYMENT_DUE])
ACTION_CANCEL = views.cancel_action(RoleType.COMMITTEE_ADMIN, [STATE_CHECKING])

ACTION_CREATE = views.create_action(RoleType.COMMITTEE_ADMIN)
ACTION_UPDATE = views.update_action(RoleType.COMMITTEE_ADMIN, [STATE_CHECKING])

ACTION_ADVANCE_PAID = views.StateAction('advance_paid', 'Paid', RoleType.PAYMENT_ADMIN,
                                   PurchaseModel.perform_advance_paid, [STATE_ADVANCE_PENDING])

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
    model = PurchaseModel(new_purchase, fund.committee)
    add_purchase_form(request.form, model, ACTION_CREATE)
    property_list = (supplier_field, properties.StringProperty('quote_amount'),
                     po_number_field, state_field)
    purchase_list = db.Purchase.query(ancestor=fund.key).fetch()
    return views.view_std_entity_list(model, 'Purchase List', ACTION_CREATE, property_list,
                                      purchase_list, parent=fund)

def load_purchase_model(db_id, request_data):
    purchase = data_models.lookup_entity(db_id)
    fund = data_models.get_parent(purchase)
    model = PurchaseModel(purchase, fund.committee)
    add_purchase_form(request_data, model, ACTION_UPDATE)
    invoice_form = InvoicedAmountForm(request_data)
    model.add_form(ACTION_INVOICED.name, invoice_form)
    advance_form = AdvanceAmountForm(request_data)
    model.add_form(ACTION_ADVANCE.name, advance_form)
    return model
    
@app.route('/purchase/<db_id>', methods=['GET', 'POST'])
def view_purchase(db_id):
    model = load_purchase_model(db_id, request.form)
    action_list = [ACTION_UPDATE, ACTION_CHECKED, ACTION_ORDERED, ACTION_ADVANCE, ACTION_PAID, ACTION_CANCEL]
    if request.method == 'POST'and views.handle_post(model, action_list + [ACTION_ADVANCE_PAID]):
        return redirect(request.base_url)
    purchase = model.entity
    fund = data_models.get_parent(purchase)
    breadcrumbs = views.view_breadcrumbs(fund, 'Purchase')
    property_list = [po_number_field, state_field, invoiced_amount_field, invoice_transferred_field, creator_field,
            supplier_field, quote_amount_field, description_field]
    content_list = [views.view_entity(purchase, property_list, 1)]
    if purchase.advance is not None:
        sub_heading = renderers.sub_heading('Advance Payment')
        advance_button = ACTION_ADVANCE_PAID.render(model)
        advance_fields = (advance_amount_field, advance_paid_field, advance_transferred_field)
        advance_grid = views.view_entity(purchase, advance_fields)
        content_list = content_list + [sub_heading, advance_button, advance_grid]
    content_list.append(views.view_entity_history(purchase.key))
    title = 'Purchase ' + purchase.po_number if purchase.po_number is not None else ""
    buttons = views.view_actions(action_list, model)
    user_controls = views.view_user_controls(model)
    content = renderers.render_div(*content_list)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbs, user=user_controls,
                           buttons=buttons, content=content)
