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
    links = views.view_links(None, 
                ('Committee', 'Show Committees'),
                ('Supplier', 'Show Suppliers'),
                ('User', 'Show Users'))
    return render_template('layout.html', title='DashBoard', user=views.render_user(), links=links)

projects.add_rules(app)
grants.add_rules(app)
pledges.add_rules(app)
supplier_funds.add_rules(app)
users.add_rules(app)
roles.add_rules(app)
partners.add_rules(app)
