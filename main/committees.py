#_*_ coding: UTF-8 _*_

from flask import url_for
from application import app

import data_models
import renderers
import properties
import views

committee_field_list = (properties.StringProperty('name'), )

@app.route('/committee_list', methods=['GET'])
def view_committee_list():
    breadcrumbs = views.view_breadcrumbs(None)
    supplier_field_list = (properties.StringProperty('name'), )
    committee_list = data_models.get_committee_list()
    entity_table = views.render_entity_list(committee_list, committee_field_list)
    user_controls = views.view_user_controls(model)
    return views.render_view('Committee List', user_controls, breadcrumbs, entity_table)

@app.route('/committee/<db_id>', methods=['GET'])
def view_committee(db_id):
    committee = data_models.lookup_committee(db_id)
    breadcrumbs = views.view_breadcrumbs(None, 'Committee')
    content = views.render_entity(committee, committee_field_list)
    links = views.view_links(committee, ('Fund', 'Show Funds'))        
    title = 'Committee ' + committee.name
    user_controls = views.view_user_controls(model)
    return views.render_view(title, user_controls, breadcrumbs, content, links)
