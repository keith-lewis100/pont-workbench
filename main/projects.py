#_*_ coding: UTF-8 _*_

from flask.views import View
import wtforms

import model
import renderers
import custom_fields
import views

class ProjectForm(renderers.EntityRenderer):
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
        return [ renderers.render_button('Show Grants', url='./grants')]

