#_*_ coding: UTF-8 _*_
from flask import Flask, render_template, redirect, url_for, request
import logging
import wtforms
import dummy_model
import renderers

app = Flask(__name__)

class ProjectForm(renderers.EntityRenderer):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class MoneyForm(renderers.EntityRenderer):
    currency = wtforms.SelectField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                                  widget=renderers.radio_field_widget)
    value = wtforms.DecimalField()

class GrantForm(renderers.EntityRenderer):
    amount = wtforms.FormField(MoneyForm, widget=renderers.form_field_widget)

@app.route('/')
def home():
    project_url = '123456'
    return redirect(url_for('view_project', id=project_url))
    
@app.route('/project/<id>/', methods=['GET'])
def view_project(id):
    app.logger.debug('view_project id=' + id)
    project = { 'name' : 'OVC-001', 'state': 'ACTIVE' }
    return render_template('project.html', entity=project)

@app.route('/project/<id>/grants', methods=['GET', 'POST'])
def view_grant_list(id):
    grant = dummy_model.create_grant()
    form = GrantForm(request.form, obj=grant)
    if request.method == 'POST' and form.validate():
        form.populate_obj(grant)
        app.logger.debug('new grant=' + unicode(grant))
        grant.put()
        return redirect(url_for('view_grant_list', id=id))
    rendered_form = form.render_fields(['amount'])
    grants = dummy_model.list_grants()
    entities = form.render_entity_list(None, grants)
    return render_template('entity_list.html', kind='Grants', entities=entities, create_form=rendered_form)
