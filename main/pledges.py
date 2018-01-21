#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views
import states
       
PLEDGE_PENDING = states.State(0, 'Pending', ('state-change', 1), ('update',))
PLEDGE_FULFILLED = states.State(1, 'Fulfilled', ('state-change', 2))
PLEDGE_BOOKED = states.State(2, 'Booked')

pledgeStates = [PLEDGE_PENDING, PLEDGE_FULFILLED, PLEDGE_BOOKED]

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class PledgeForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)
    
class Pledge(views.EntityType):
    def __init__(self):
        self.name = 'Pledge'
        self.formClass = PledgeForm

    def get_state(self, index):
        return pledgeStates[index]
        
    def create_entity(self, parent):
        return model.create_pledge(parent)

    def load_entities(self, parent):
        return model.list_pledges(parent)
        
    def title(self, entity):
        return 'Pledge'
    
class PledgeListView(views.ListView):
    def __init__(self):
        self.entityType = Pledge()
        
    def get_fields(self, form):
        ref_id = views.ReadOnlyField('ref_id', 'Reference')
        state = views.StateField(pledgeStates)
        return (ref_id, form._fields['amount'], state)

class PledgeView(views.EntityView):
    def __init__(self):
        self.entityType = Pledge()
        self.actions = [(1, 'Fulfill'), (2, 'Book')]
        
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
    app.add_url_rule('/pledge/<db_id>/menu', view_func=views.MenuView.as_view('handle_pledge_menu'))
