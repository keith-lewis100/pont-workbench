#_*_ coding: UTF-8 _*_

from flask import redirect, request, url_for
from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views
import logging

class MoneyForm(wtforms.Form):
    value = wtforms.IntegerField()


class PledgeForm(wtforms.Form):
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)
    
class PledgeListView(views.ListView):
    def __init__(self):
        self.kind = 'Pledges'
        self.formClass = PledgeForm
        
    def create_entity(self, db_id):
        return model.create_pledge(db_id)

    def load_entities(self, db_id):
        return model.list_pledges(db_id)
        
    def get_fields(self, entity):
        form = PledgeForm()
        state = views.ReadOnlyField('state', 'State')
        return (form._fields['amount'], state)

class PledgeView(views.EntityView):
    def __init__(self):
        self.kind = 'Pledge'
        
    def get_fields(self, entity):
        form = PledgeForm()
        state = views.ReadOnlyField('state', 'State')
        return (form._fields['amount'], state)
        
    def title(self, entity):
        return ""

    def get_menu(self, entity):
        enabled = model.is_action_allowed('fulfill', entity)
        fulfilled = renderers.render_button('Fulfill', name='action', value='fulfill', 
                        disabled=not enabled)
        return renderers.render_form(fulfilled, action='./menu')
        
class ProjectMenuView(View):
    methods = ['POST']
    
    def dispatch_request(self, db_id):
        entity = model.lookup_entity(db_id)
        action = request.form['action']
        model.perform_action(action, entity)
        return redirect('/pledge/' + db_id)

def add_rules(app):
    app.add_url_rule('/pledge_list/<db_id>', view_func=PledgeListView.as_view('view_pledge_list'))
    app.add_url_rule('/pledge/<db_id>/', view_func=PledgeView.as_view('view_pledge'))
    app.add_url_rule('/pledge/<db_id>/menu', view_func=ProjectMenuView.as_view('handle_pledge_menu'))
