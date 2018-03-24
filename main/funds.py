#_*_ coding: UTF-8 _*_

from flask import url_for
import wtforms

import db
import model
import renderers
import custom_fields
import views
from role_types import RoleType

class FundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    committee = custom_fields.SelectField(choices=model.committee_labels)
    description = wtforms.TextAreaField()

class FundModel(model.EntityModel):
    def __init__(self):
        model.EntityModel.__init__(self, 'Fund', RoleType.FUND_ADMIN)

    def create_entity(self, parent):
        return db.Fund()

    def load_entities(self, parent):
        return db.Fund.query().fetch()
        
    def title(self, entity):
        return 'Fund ' + entity.name

fund_model = FundModel()

class FundListView(views.ListView):
    def __init__(self):
        views.ListView.__init__(self, fund_model, FundForm)
        
    def get_fields(self, form):
        return (form._fields['name'],form._fields['committee'])
        
class FundView(views.EntityView):
    def __init__(self):
        views.EntityView.__init__(self, fund_model, FundForm)
        
    def get_fields(self, form):
        return form._fields.values()
        
    def get_links(self, entity):
        projects_url = url_for('view_project_list', db_id=entity.key.urlsafe())
        showProjects = renderers.render_link('Show Projects', projects_url, class_="button")
        transfers_url = url_for('view_internaltransfer_list', db_id=entity.key.urlsafe())
        showTransfers = renderers.render_link('Show Transfers', transfers_url, class_="button")        
        return [showProjects, showTransfers]

def add_rules(app):
    app.add_url_rule('/fund_list', view_func=FundListView.as_view('view_fund_list'))
    app.add_url_rule('/fund/<db_id>/', view_func=FundView.as_view('view_fund'))        
