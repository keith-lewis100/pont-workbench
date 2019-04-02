#_*_ coding: UTF-8 _*_

from flask import url_for, render_template
from application import app

import renderers
import views

import funds
import projects
import grants
import pledges
import suppliers
import supplier_funds
import internal_transfers
import purchases
import users
import roles
import partners
import foreign_transfer
import committees

@app.route('/')
def home():
    showCommittees = views.render_link('Committee', 'Show Committees')
    showSuppliers = views.render_link('Supplier', 'Show Suppliers')
    showUsers = views.render_link('User', 'Show Users')
    links = renderers.render_nav(showCommittees, showSuppliers, showUsers)
    return render_template('layout.html', title='DashBoard', user=views.render_user(), main=links)

projects.add_rules(app)
grants.add_rules(app)
pledges.add_rules(app)
supplier_funds.add_rules(app)
users.add_rules(app)
roles.add_rules(app)
partners.add_rules(app)
