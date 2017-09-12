from flask import render_template, redirect, url_for, request
from flask.views import View
import renderers

class ListView(View):
    methods = ['GET', 'POST']
        
    def dispatch_request(self, **kwargs):
        entity = self.create_entity(**kwargs)
        form = self.formClass(request.form, obj=entity)
        if request.method == 'POST' and form.validate():
            form.populate_obj(entity)
            entity.put()
            return redirect(request.base_url)
            
        rendered_form = renderers.render_fields(*form._fields.values())
        entities = self.load_entities(**kwargs)
        entity_table = renderers.render_entity_list(entities, *form._fields.values())
        return render_template('entity_list.html',  kind=self.kind, entity_table=entity_table, 
                new_entity_form=rendered_form)
        
class EntityView(View):
    def dispatch_request(self, **kwargs):
        entity = self.lookup_entity(**kwargs)
        form = self.formClass()
        menu = self.get_menu()
        rendered_entity = renderers.render_entity(entity, *form._fields.values())
        return render_template('entity.html', kind=self.kind, name=entity.name, menu=menu, 
                        entity=rendered_entity)
