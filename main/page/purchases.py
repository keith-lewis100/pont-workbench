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
STATE_ADVANCE_PENDING = 4 # derived state
STATE_ADVANCED = 5 # derived state
STATE_PAYMENT_DUE = 6 # derived state

state_labels = ['Closed', 'Checking', 'Ready', 'Ordered', 'Advance Payment Pending', 'Advance Paid', 'Payment Due']

supplier_field = properties.KeyProperty('supplier')
quote_amount_field = properties.StringProperty('quote_amount')
description_field = properties.StringProperty('description')
state_field = properties.SelectProperty('state_index', 'State', enumerate(state_labels))
po_number_field = properties.StringProperty('po_number', 'PO number')
creator_field = properties.KeyProperty('creator')

payment_amount_field = properties.StringProperty('amount', 'Payment Amount')
payment_paid_field = properties.StringProperty('paid', 'Paid')
payment_type_field = properties.StringProperty(lambda e: e.payment_type.capitalize(), 'Type')
payment_transferred_field = properties.StringProperty(lambda e: data_models.calculate_transferred_amount(e), 
                                    'Transferred Amount')

class PurchaseModel(data_models.Model):
    def __init__(self, entity, committee, payments):
        super(PurchaseModel, self).__init__(entity, committee, db.Purchase)
        self.payments = payments
 
    def perform_checked(self, action_name):
        entity = self.entity
        entity.state_index = STATE_READY
        ref = data_models.get_next_ref()
        entity.po_number = 'MB%04d' % ref
        entity.put()
        self.email_and_audit(action_name, "Check performed")
        return True

    def perform_ordered(self, action_name):
        self.entity.state_index = STATE_ORDERED
        self.entity.put()
        self.email_and_audit(action_name, "Ordered performed")
        return True

    def perform_create_payment(self, action_name):
        form = self.get_form(action_name)
        if not form.validate():
            return False
        payment = db.PurchasePayment(parent=self.entity.key)
        payment.supplier = self.entity.supplier
        payment.payment_type = action_name
        payment.transfer = None
        form.populate_obj(payment)
        payment.put()
        self.email_and_audit(action_name, "%s amount=%s" % (action_name.capitalize(), payment.amount))
        return True

    def perform_paid(self, action_name):
        payment_type = action_name[5:] # remove 'paid_' prefix
        payment = self.payments[payment_type]
        payment.paid = True
        payment.put()
        if payment_type == 'invoice':
            self.entity.state_index = data_models.STATE_CLOSED
            self.entity.put()
        self.email_and_audit(action_name, "Paid %s" % payment_type)
        return True

    def get_state(self):
        purchase = self.entity
        invoice = self.payments.get('invoice')
        advance = self.payments.get('advance')
        state = purchase.state_index
        if state == STATE_ORDERED:        
            if  invoice != None and not invoice.paid:
                return STATE_PAYMENT_DUE
            if advance != None:
                return STATE_ADVANCED  if advance.paid else STATE_ADVANCE_PENDING
        return state

ACTION_CHECKED = views.StateAction('checked', 'Funds Checked', RoleType.FUND_ADMIN,
                                   PurchaseModel.perform_checked, [STATE_CHECKING])
ACTION_ORDERED = views.StateAction('ordered', 'Ordered', RoleType.COMMITTEE_ADMIN,
                                   PurchaseModel.perform_ordered, [STATE_READY])
ACTION_INVOICE = views.StateAction('invoice', 'Invoiced', RoleType.COMMITTEE_ADMIN,
                               PurchaseModel.perform_create_payment, [STATE_ORDERED, STATE_ADVANCED])
ACTION_ADVANCE = views.StateAction('advance', 'Advance Payment', RoleType.COMMITTEE_ADMIN,
                              PurchaseModel.perform_create_payment, [STATE_ORDERED])
ACTION_INVOICE_PAID = views.StateAction('paid_invoice', 'Paid', RoleType.PAYMENT_ADMIN,
                                PurchaseModel.perform_paid, [STATE_PAYMENT_DUE])
ACTION_CANCEL = views.cancel_action(RoleType.COMMITTEE_ADMIN, [STATE_CHECKING, STATE_READY])

ACTION_CREATE = views.create_action(RoleType.COMMITTEE_ADMIN)
ACTION_UPDATE = views.update_action(RoleType.COMMITTEE_ADMIN, [STATE_CHECKING])

ACTION_ADVANCE_PAID = views.StateAction('paid_advance', 'Paid', RoleType.PAYMENT_ADMIN,
                                   PurchaseModel.perform_paid, [STATE_ADVANCE_PENDING])

class PurchaseForm(wtforms.Form):
    quote_amount = wtforms.FormField(custom_fields.MoneyForm, widget=custom_fields.form_field_widget)
    supplier = custom_fields.SelectField(coerce=data_models.create_key, validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

def add_purchase_form(request_data, model, action):
    form = PurchaseForm(request_data, obj=model.entity)
    supplier_list = db.Supplier.query().fetch()
    custom_fields.set_field_choices(form.supplier, supplier_list)
    model.add_form(action.name, form)

class PaymentAmountForm(wtforms.Form):
    amount = wtforms.FormField(custom_fields.MoneyForm, label='Payment Amount', widget=custom_fields.form_field_widget)

@app.route('/purchase_list/<db_id>', methods=['GET', 'POST'])
def view_purchase_list(db_id):
    fund = data_models.lookup_entity(db_id)
    new_purchase = db.Purchase(parent=fund.key)
    model = PurchaseModel(new_purchase, fund.committee, {})
    add_purchase_form(request.form, model, ACTION_CREATE)
    property_list = (state_field, po_number_field, supplier_field, properties.StringProperty('quote_amount'))
    purchase_query = db.Purchase.query(ancestor=fund.key).order(-db.Purchase.state_index,
                                                                db.Purchase.po_number)
    return views.view_std_entity_list(model, 'Purchase List', ACTION_CREATE, property_list,
                                      purchase_query, fund)

def load_purchase_model(purchase, payment_list, request_data):
    fund = data_models.get_parent(purchase)
    payments = dict([(e.payment_type, e) for e in payment_list])
    model = PurchaseModel(purchase, fund.committee, payments)
    add_purchase_form(request_data, model, ACTION_UPDATE)
    invoice_form = PaymentAmountForm(request_data)
    model.add_form(ACTION_INVOICE.name, invoice_form)
    advance_form = PaymentAmountForm(request_data)
    model.add_form(ACTION_ADVANCE.name, advance_form)
    return model
    
@app.route('/purchase/<db_id>', methods=['GET', 'POST'])
def view_purchase(db_id):
    purchase = data_models.lookup_entity(db_id)
    payment_list = db.PurchasePayment.query(ancestor=purchase.key).order(db.PurchasePayment.payment_type).fetch()
    model = load_purchase_model(purchase, payment_list, request.form)
    action_list = [ACTION_UPDATE, ACTION_CHECKED, ACTION_ORDERED, ACTION_ADVANCE, ACTION_INVOICE, ACTION_CANCEL]
    if request.method == 'POST'and views.handle_post(model, action_list + [ACTION_ADVANCE_PAID, ACTION_INVOICE_PAID]):
        return redirect(request.base_url)
    purchase = model.entity
    breadcrumbs = views.view_breadcrumbs_list(purchase)
    property_list = [po_number_field, state_field, quote_amount_field, creator_field, supplier_field, description_field]
    content_list = [views.view_entity(purchase, property_list, 1)]
    for payment in payment_list:
        sub_heading = renderers.sub_heading(payment.payment_type.capitalize() + ' Payment')
        action = ACTION_ADVANCE_PAID if payment.payment_type == 'advance' else ACTION_INVOICE_PAID
        paid_button = action.render(model)
        payment_fields = (payment_amount_field, payment_paid_field, payment_transferred_field)
        payment_grid = views.view_entity(payment, payment_fields)
        content_list = content_list + [sub_heading, paid_button, payment_grid]
    content_list.append(views.view_entity_history(purchase.key))
    title = 'Purchase ' + purchase.po_number if purchase.po_number is not None else ""
    buttons = views.view_actions(action_list, model)
    user_controls = views.view_user_controls(model)
    content = renderers.render_div(*content_list)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbs, user=user_controls,
                           buttons=buttons, content=content)
