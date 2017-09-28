#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()

class PledgeForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)
    
class PledgeListView(views.ListView):
    def __init__(self):
        self.kind = 'Pledge'
        self.formClass = PledgeForm
        
    def create_entity(self, parent):
        return model.create_pledge(parent)

    def load_entities(self, parent):
        return model.list_pledges(parent)
        
    def get_fields(self, form):
        ref_id = views.ReadOnlyField('ref_id', 'Reference')
        state = views.ReadOnlyField('state', 'State')
        return (ref_id, form._fields['amount'], state)

class PledgeView(views.EntityView):
    def __init__(self):
        self.formClass = PledgeForm
        self.actions = [(1, 'Fulfill')]
        
    def get_fields(self, form):
        state = views.ReadOnlyField('state', 'State')
        ref_id = views.ReadOnlyField('ref_id', 'Reference')
        creator = views.ReadOnlyKeyField('creator', 'Creator')
        return (ref_id, form._fields['amount'], state, creator)
        
    def title(self, entity):
        return "Pledge"

    def get_links(self, entity):
        return ""

def add_rules(app):
    app.add_url_rule('/pledge_list/<db_id>', view_func=PledgeListView.as_view('view_pledge_list'))
    app.add_url_rule('/pledge/<db_id>/', view_func=PledgeView.as_view('view_pledge'))
    app.add_url_rule('/pledge/<db_id>/menu', view_func=views.MenuView.as_view('handle_pledge_menu'))
