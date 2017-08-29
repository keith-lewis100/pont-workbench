#_*_ coding: UTF-8 _*_
from flask import Flask, render_template, redirect, url_for, request
import logging
import wtforms
import html;
import dummy_model
import view_model

app = Flask(__name__)

class ProjectForm(view_model.ViewModel):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class MoneyForm(view_model.ViewModel):
    currency = wtforms.RadioField(choices=[('sterling', u'£'), ('ugx', u'Ush')],
                                  widget=html.render_radio_field)
    value = wtforms.DecimalField()

class GrantForm(view_model.ViewModel):
    amount = wtforms.FormField(MoneyForm, widget=view_model.form_field_widget)

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
        app.logger.debug('new grant=' + str(grant))
        grant.put()
        return redirect(url_for('view_grant_list', id=id))
    rendered_form = form.render_fields(['amount'])
    grants = dummy_model.list_grants()
    return render_template('grants.html', entities=grants, create_form=rendered_form)
