#_*_ coding: UTF-8 _*_

from flask import url_for
from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views

class FundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    description = wtforms.TextAreaField()

class PontFundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    committee = wtforms.SelectField(choices=[
        ('PHC', 'PrimaryHealth'),
        ('EDU', 'SecondaryHealth'),
        ('LIV', 'Livelihoods'), 
        ('ENG', 'Engineering'),
        ('EDU', 'Education'), 
        ('CHU', 'Churches'), 
        ('WEC', 'Wildlife Centre')])
    description = wtforms.TextAreaField()

class FundListView(views.ListView):
    def __init__(self, pont_only):
        self.kind = 'Fund'
        self.formClass = FundForm
        if pont_only:
            self.formClass = PontFundForm
        
    def create_entity(self, parent):
        return model.create_fund(parent)

    def load_entities(self, parent):
        return model.list_funds(parent)

    def get_fields(self, form):
        if self.formClass == PontFundForm:
            return (form._fields['name'],form._fields['committee'])
        return (form._fields['name'],)
        
    def url_for_entity(self, entity):
        if self.formClass == PontFundForm:
            return '/pont_fund/%s/' % entity.key.urlsafe()
        return '/fund/%s/' % entity.key.urlsafe()

class FundView(views.EntityView):
    def __init__(self, pont_only):
        self.formClass = FundForm
        if pont_only:
            self.formClass = PontFundForm
        self.actions = []
        
    def get_fields(self, form):
        return form._fields.values()
    
    def title(self, entity):
        return'Fund ' + entity.name
        
    def get_links(self, entity):
        if entity.key.parent():
            return ""
        projects_url = url_for('view_project_list', db_id=entity.key.urlsafe())
        showProjects = renderers.render_link('Show Projects', projects_url)
        transfers_url = url_for('view_transfer_list', db_id=entity.key.urlsafe())
        showTransfers = renderers.render_link('Show Transfers', transfers_url)        
        return renderers.render_nav(showProjects, showTransfers)

def add_rules(app):
    app.add_url_rule('/pont_fund_list', view_func=FundListView.as_view('view_pont_fund_list', True))
    app.add_url_rule('/fund_list/<db_id>', view_func=FundListView.as_view('view_fund_list', False))
    app.add_url_rule('/pont_fund/<db_id>/', view_func=FundView.as_view('view_pont_fund', True))        
    app.add_url_rule('/fund/<db_id>/', view_func=FundView.as_view('view_fund', False))        
