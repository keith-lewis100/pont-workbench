from flask import render_template, redirect, request, url_for
from flask.views import View
import renderers
import model

class Label:
    def __init__(self, text):
        self.text = text

class ReadOnlyField:
    def __init__(self, name, label):
        self.name = name
        self.label = Label(label)

def url_for_entity(entity):
    key = entity.key
    return '/%s/%s/' % (key.kind().lower(), key.urlsafe())

class ListView(View):
    methods = ['GET', 'POST']
        
    def dispatch_request(self, db_id=None):
        entity = self.create_entity(db_id)
        form = self.formClass(request.form, obj=entity)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            entity.put()
            return redirect(request.base_url)
            
        rendered_form = renderers.render_fields(*form._fields.values())
        entity_list = self.load_entities(db_id)
        fields = self.get_fields(entity)
        rows = []
        for e in entity_list:
            url = url_for_entity(e)
            rows.append(renderers.render_row(e, url, *fields))
        entity_table = renderers.render_entity_list(rows, *fields)
        return render_template('entity_list.html',  kind=self.kind, entity_table=entity_table, 
                new_entity_form=rendered_form)
        
class EntityView(View):
    def dispatch_request(self, db_id):
        entity = model.lookup_entity(db_id)
        fields = self.get_fields(entity)
        menu = self.get_menu(entity)
        rendered_entity = renderers.render_entity(entity, *fields)
        name = self.title(entity)
        return render_template('entity.html', kind=entity.key.kind(), name=name, menu=menu, 
                        entity=rendered_entity)

class MenuView(View):
    methods = ['POST']
    
    def dispatch_request(self, db_id):
        entity = model.lookup_entity(db_id)
        action = request.form['action']
        model.perform_action(action, entity)
        return redirect(url_for_entity(entity))
