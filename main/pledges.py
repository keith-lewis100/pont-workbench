#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import readonly_fields
import views
from role_types import RoleType
from projects import project_model

PLEDGE_PENDING = 1
#states.State('Pending', True, {'fulfilled': RoleType.INCOME_ADMIN}) # 1
PLEDGE_FULFILLED = 2
#states.State('Fulfilled', False, {'booked': RoleType.FUND_ADMIN}) # 2
PLEDGE_CLOSED = 3
#states.State('Closed') # 0

ACTION_FULFILLED = model.Action('fulfilled', 'Fulfilled', RoleType.INCOME_ADMIN, PLEDGE_FULFILLED)
ACTION_BOOKED = model.Action('booked', 'Booked', RoleType.FUND_ADMIN, PLEDGE_CLOSED)

state_field = readonly_fields.StateField('Closed', 'Pending', 'Fulfilled')

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class PledgeForm(wtforms.Form):
    description = wtforms.TextAreaField()
    amount = wtforms.FormField(MoneyForm, widget=custom_fields.form_field_widget)
    
class PledgeModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Pledge', RoleType.COMMITTEE_ADMIN, PLEDGE_PENDING)

    def create_entity(self, parent):
        return db.Pledge(parent=parent.key)

    def load_entities(self, parent):
        return db.Pledge.query(ancestor=parent.key).fetch()
        
    def title(self, entity):
        return 'Pledge'
        
    def perform_create(self, entity, user):
        ref = model.get_next_ref()
        entity.ref_id = 'PL%04d' % ref
        model.EntityModel.perform_create(self, entity, user)

pledge_model = PledgeModel()
        
class PledgeListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, pledge_model)
        
    def create_form(self, request_input, entity):
        return PledgeForm(request_input, obj=entity)

    def get_fields(self, form):
        ref_id = readonly_fields.ReadOnlyField('ref_id', 'Reference')
        return (ref_id, readonly_fields.ReadOnlyField('amount'), state_field)

class PledgeView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, pledge_model, ACTION_FULFILLED, ACTION_BOOKED)
        
    def create_form(self, request_input, entity):
        return PledgeForm(request_input, obj=entity)
        
    def get_fields(self, form):
        ref_id = readonly_fields.ReadOnlyField('ref_id', 'Reference')
        creator = readonly_fields.ReadOnlyKeyField('creator')
        return map(readonly_fields.create_readonly_field, form._fields.keys(), form._fields.values()) + [ref_id, state_field, creator]

    def get_links(self, entity):
        return []

def add_rules(app):
    app.add_url_rule('/pledge_list/<db_id>', view_func=PledgeListView.as_view('view_pledge_list'))
    app.add_url_rule('/pledge/<db_id>/', view_func=PledgeView.as_view('view_pledge'))
