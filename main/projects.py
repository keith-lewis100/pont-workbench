#_*_ coding: UTF-8 _*_

from flask.views import View, request
import wtforms

import model
import renderers
import custom_fields
import views
import logging

class ProjectForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    dest_fund = custom_fields.KeyPropertyField('Destination Fund', 
                  query=model.cap_fund_query())

class ProjectListView(views.ListView):
    def __init__(self):
        self.kind = 'Projects'
        self.formClass = ProjectForm
        
    def create_entity(self):
        return model.create_project()

    def load_entities(self):
        return model.list_projects()

class ProjectView(views.EntityView):
    def __init__(self):
        self.kind = 'Project'
        self.formClass = ProjectForm
        
    def lookup_entity(self, project_id):
        return  model.lookup_entity(('Project', project_id))
        
    def get_menu(self):
        showGrants = renderers.render_link('Show Grants', url='./grants', class_="button")
        approve = renderers.render_button('Approve', name='action', value='approve', disabled=True)
        return renderers.render_form(showGrants, approve, action='./menu')

class ProjectMenuView(View):
    methods = ['POST']
    
    def dispatch_request(self, project_id):
        return "handling action %s for project %s" % (request.form['action'], project_id)

def add_rules(app):
    app.add_url_rule('/projects', view_func=ProjectListView.as_view('view_project_list'))
    app.add_url_rule('/project/<project_id>/', view_func=ProjectView.as_view('view_project'))        
    app.add_url_rule('/project/<project_id>/menu', view_func=ProjectMenuView.as_view('handle_project_menu'))
