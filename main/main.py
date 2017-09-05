#_*_ coding: UTF-8 _*_

from flask import Flask, render_template, redirect, url_for, request
from flask.views import View
#from flask.ext.principal import Principal, Identity, AnonymousIdentity, identity_changed
import wtforms

import model
import renderers
import custom_fields

app = Flask(__name__)

class ProjectForm(renderers.EntityRenderer):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])
    dest_fund = custom_fields.KeyPropertyField('Destination Fund', 
                  query=model.fund_query(('Organisation', 2)))

class MoneyForm(renderers.EntityRenderer):
    currency = wtforms.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                    widget=renderers.radio_field_widget)
    value = wtforms.DecimalField()

class GrantForm(renderers.EntityRenderer):
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)

@app.route('/')
def home():
    return redirect(url_for('view_project_list'))
    
class ListView(View):
    methods = ['GET', 'POST']
        
    def dispatch_request(self, **kwargs):
        entity = self.create_entity(**kwargs)
        form = self.formClass(request.form, obj=entity)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            entity.put()
            return redirect(request.base_url)
            
        rendered_form = form.render_fields()
        entities = self.load_entities(**kwargs)
        entity_table = form.render_entity_list(None, entities)
        return render_template('entity_list.html',  kind=self.kind, entity_table=entity_table, 
                new_entity_form=rendered_form)
        
class ProjectList(ListView):
    def __init__(self):
        self.kind = 'Projects'
        self.formClass = ProjectForm
        
    def create_entity(self):
        return model.create_project()

    def load_entities(self):
        return model.list_projects()

app.add_url_rule('/projects', view_func=ProjectList.as_view('view_project_list'))

class GrantList(ListView):
    def __init__(self):
        self.kind = 'Grants'
        self.formClass = GrantForm
        
    def create_entity(self, project_id):
        return model.create_grant(('Project', project_id))

    def load_entities(self, project_id):
        return model.list_grants(('Project', project_id))

app.add_url_rule('/project/<project_id>/grants', view_func=GrantList.as_view('view_grant_list'))

@app.route('/project/<project_id>/', methods=['GET'])
def view_project(project_id):
    project = model.lookup_entity(('Project', project_id))
    form = ProjectForm()
    menu = [ renderers.render_button('Show Grants', url='./grants')]
    entity = form.render_entity(None, project)
    return render_template('entity.html', kind='Project', menu=menu, entity=entity)

@app.route('/project/<project_id>/grant/<grant_id>', methods=['GET'])
def view_grant(project_id, grant_id):
    grant = model.lookup_entity(('Project', project_id), ('Grant', grant_id))
    form = GrantForm(request.form, obj=grant)
    entity = form.render_entity(None, grant)
    menu = []
    return render_template('entity.html', kind='Grant', menu=menu, entity=entity)

@app.route('/supplier/<supplier_id>')
def view_supplier_payments(supplier_id):
    payments = model.list_supplier_payments(('Organisation', supplier_id))
    entities = form.render_entity_list(None, payments)
    return render_template('entity_list.html', kind='Payments', entities=entities, create_form=rendered_form)
    