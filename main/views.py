from flask import render_template, redirect, request
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
        entities = self.load_entities(db_id)
        fields = self.get_fields(entity)
        entity_table = renderers.render_entity_list(entities, *fields)
        return render_template('entity_list.html',  kind=self.kind, entity_table=entity_table, 
                new_entity_form=rendered_form)
        
class EntityView(View):
    def dispatch_request(self, db_id):
        entity = model.lookup_entity(db_id)
        fields = self.get_fields(entity)
        menu = self.get_menu(entity)
        rendered_entity = renderers.render_entity(entity, *fields)
        name = self.title(entity)
        return render_template('entity.html', kind=self.kind, name=name, menu=menu, 
                        entity=rendered_entity)
