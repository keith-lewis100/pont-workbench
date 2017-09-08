#_*_ coding: UTF-8 _*_

from flask import Flask, redirect

import projects
import grants
import suppliers
app = Flask(__name__)

@app.route('/')
def home():
    return redirect('/projects')

app.add_url_rule('/projects', view_func=projects.ProjectListView.as_view('view_project_list'))
app.add_url_rule('/project/<project_id>/grants', view_func=grants.GrantListView.as_view('view_grant_list'))
app.add_url_rule('/project/<project_id>/', view_func=projects.ProjectView.as_view('view_project'))        
app.add_url_rule('/project/<project_id>/grant/<grant_id>/', view_func=grants.GrantView.as_view('view_grant'))
app.add_url_rule('/suppliers', view_func=suppliers.SupplierListView.as_view('view_supplier_list'))
app.add_url_rule('/supplier/<supplier_id>', view_func=suppliers.SupplierView.as_view('view_supplier'))
