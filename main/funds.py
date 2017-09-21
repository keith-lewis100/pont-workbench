#_*_ coding: UTF-8 _*_

from flask import redirect, request, url_for
from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views
import logging

class FundForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class FundListView(views.ListView):
    def __init__(self):
        self.kind = 'Fund'
        self.formClass = FundForm
        
    def create_entity(self, db_id):
        return model.create_fund(db_id)

    def load_entities(self, db_id):
        return model.list_funds(db_id)

    def get_fields(self, form):
        return (form._fields['name'],)

class FundView(views.EntityView):
    def __init__(self):
        self.formClass = FundForm
        self.actions = []
        
    def get_fields(self, form):
        return (form._fields['name'],)
    
    def title(self, entity):
        return'Fund ' + entity.name
        
    def get_links(self, entity):
        projects_url = url_for('view_project_list', db_id=entity.key.urlsafe())
        if entity.key.parent():
            return ""
        showProjects = renderers.render_link('Show Projects', url=projects_url, class_="button")
        return renderers.render_div(showProjects)

def add_rules(app):
    app.add_url_rule('/pont_fund_list', view_func=FundListView.as_view('view_pont_fund_list'))
    app.add_url_rule('/fund_list/<db_id>', view_func=FundListView.as_view('view_fund_list'))
    app.add_url_rule('/fund/<db_id>/', view_func=FundView.as_view('view_fund'))        
