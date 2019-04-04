#_*_ coding: UTF-8 _*_

from flask import render_template
from application import app

import data_models
import properties
import views

committee_field_list = (properties.StringProperty('name'), )

@app.route('/committee_list', methods=['GET'])
def view_committee_list():
    breadcrumbs = views.view_breadcrumbs(None)
    supplier_field_list = (properties.StringProperty('name'), )
    committee_list = data_models.get_committee_list()
    entity_table = views.view_entity_list(committee_list, committee_field_list)
    user_controls = views.view_user_controls(model)
    return render_template('layout.html', title='Committee List', breadcrumbs=breadcrumbs, user=user_controls,
                           content=entity_table)

@app.route('/committee/<db_id>', methods=['GET'])
def view_committee(db_id):
    committee = data_models.lookup_committee(db_id)
    breadcrumbs = views.view_breadcrumbs(None, 'Committee')
    grid = views.view_entity(committee, committee_field_list)
    links = views.view_links(committee, ('Fund', 'Show Funds'))        
    title = 'Committee ' + committee.name
    user_controls = views.view_user_controls(model)
    return render_template('layout.html', title=title, breadcrumbs=breadcrumbs, user=user_controls,
                           links=links, content=grid)
