#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import db
import model
import renderers
import custom_fields
import views
import states
from role_types import RoleType
from projects import project_model

PLEDGE_PENDING = states.State('Pending', True, False, {1: RoleType.INCOME_ADMIN}) # 0
PLEDGE_FULFILLED = states.State('Fulfilled', False, False, {2: RoleType.FUND_ADMIN}) # 1
PLEDGE_BOOKED = states.State('Booked') # 2

pledgeStates = [PLEDGE_PENDING, PLEDGE_FULFILLED, PLEDGE_BOOKED]

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class PledgeForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)
    
class PledgeModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Pledge', RoleType.COMMITTEE_ADMIN, project_model, pledgeStates)

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
        views.ListView.__init__(self, pledge_model, PledgeForm)
        
    def get_fields(self, form):
        ref_id = views.ReadOnlyField('ref_id', 'Reference')
        state = views.StateField(pledgeStates)
        return (ref_id, form._fields['amount'], state)

class PledgeView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, pledge_model, PledgeForm, (1, 'Fulfill'), (2, 'Book'))
        
    def get_fields(self, form):
        state = views.StateField(pledgeStates)
        ref_id = views.ReadOnlyField('ref_id', 'Reference')
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        return (ref_id, form._fields['amount'], state, creator)

    def get_links(self, entity):
        return []

def add_rules(app):
    app.add_url_rule('/pledge_list/<db_id>', view_func=PledgeListView.as_view('view_pledge_list'))
    app.add_url_rule('/pledge/<db_id>/', view_func=PledgeView.as_view('view_pledge'))
    app.add_url_rule('/pledge/<db_id>/menu', view_func=views.MenuView.as_view('handle_pledge_menu', pledge_model))
