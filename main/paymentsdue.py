#_*_ coding: UTF-8 _*_

from flask import url_for
from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import views

class MoneyForm(wtforms.Form):
    currency = custom_fields.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.IntegerField(validators=[wtforms.validators.NumberRange(min=50)])

class PaymentsDueForm(wtforms.Form):
    creator = custom_fields.KeyPropertyField("Requestor Name")
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)

class PaymentsDueModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'PaymentsDue', None)

    def create_entity(self, parent):
        return None

    def load_entities(self, parent):
        return db.Grant.query().fetch()
        
    def title(self, entity):
        return 'PaymentsDue ' + entity.name

paymentsdue_model = PaymentsDueModel()

class PaymentsDueView(views.ListViewNoCreate):
    def __init__(self):
        views.ListViewNoCreate.__init__(self, paymentsdue_model, PaymentsDueForm)
 
    def get_fields(self, form):
        return form._fields.values()

def add_rules(app):
    app.add_url_rule('/paymentsdue', view_func=PaymentsDueView.as_view('view_paymentsdue_list'))
