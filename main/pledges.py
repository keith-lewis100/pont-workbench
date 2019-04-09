#_*_ coding: UTF-8 _*_

import wtforms

import db
import data_models
import custom_fields
import properties
import views
from role_types import RoleType

STATE_PENDING = 1
STATE_FULFILLED = 2

state_labels = ['Closed', 'Pending', 'Fulfilled']

def perform_create(model, action_name):
        form = self.get_form(action_name)
        if not form.validate():
            return False
        entity = model.entity
        form.populate_obj(entity)
        ref = data_models.get_next_ref()
        entity.ref_id = 'PL%04d' % ref
        entity.creator = user.key
        entity.put()
        model.audit(action_name, "Create performed")
        return True

def perform_fulfilled(model, action_name):
    model.entity.state_index = STATE_FULFILLED
    model.entity.put()
    model.audit(action_name, 'Fulfilled performed')

ACTION_FULFILLED = views.StateAction('fulfilled', 'Fulfilled', RoleType.INCOME_ADMIN,
                                     perform_fulfilled, [STATE_PENDING])
ACTION_BOOKED = views.StateAction('booked', 'Booked', RoleType.FUND_ADMIN,
                                  data_models.Model.perform_close, [STATE_FULFILLED])
ACTION_UPDATE = views.update_action(RoleType.COMMITTEE_ADMIN, [STATE_PENDING])
ACTION_CREATE = views.Action('create', 'New', RoleType.COMMITTEE_ADMIN, perform_create)

state_field = properties.SelectProperty('state_index', 'State', enumerate(state_labels))

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class PledgeForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=custom_fields.form_field_widget)
    description = wtforms.TextAreaField()

class PledgeListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, 'Pledge', ACTION_CREATE)

    def load_entities(self, parent):
        return db.Pledge.query(ancestor=parent.key).fetch()

    def create_entity(self, parent):
        return db.Pledge(parent=parent.key)
        
    def create_form(self, request_input, entity):
        return PledgeForm(request_input, obj=entity)

    def get_fields(self, form):
        ref_id = properties.StringProperty('ref_id', 'Reference')
        return (ref_id, properties.StringProperty('amount'), state_field)

class PledgeView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, ACTION_UPDATE, 1, ACTION_FULFILLED, ACTION_BOOKED)

    def title(self, entity):
        return 'Pledge'
        
    def create_form(self, request_input, entity):
        return PledgeForm(request_input, obj=entity)
        
    def get_fields(self, form):
        ref_id = properties.StringProperty('ref_id', 'Reference')
        creator = properties.KeyProperty('creator')
        return [ref_id, state_field, creator] + map(properties.create_readonly_field, 
                    form._fields.keys(), form._fields.values())

def add_rules(app):
    app.add_url_rule('/pledge_list/<db_id>', view_func=PledgeListView.as_view('view_pledge_list'))
    app.add_url_rule('/pledge/<db_id>/', view_func=PledgeView.as_view('view_pledge'))
