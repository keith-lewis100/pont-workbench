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
    committee_url = url_for('view_committee_list')
    showCommittees = renderers.render_link('Show Committees', committee_url, class_="button")
    suppliers_url = url_for('view_supplier_list')        
    showSuppliers = renderers.render_link('Show Suppliers', suppliers_url, class_="button")
    users_url = url_for('view_user_list')        
    showUsers = renderers.render_link('Show Users', users_url, class_="button")
    links = renderers.render_nav(showCommittees, showSuppliers, showUsers)
    return render_template('layout.html', title='DashBoard', user=views.render_user(), main=links)

funds.add_rules(app)
projects.add_rules(app)
grants.add_rules(app)
pledges.add_rules(app)
supplier_funds.add_rules(app)
internal_transfers.add_rules(app)
users.add_rules(app)
roles.add_rules(app)
partners.add_rules(app)
