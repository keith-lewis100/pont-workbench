import renderers
import views

class UserForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.InputRequired()])

class UserListView(views.ListView):
    def __init__(self):
        self.kind = 'User'
        self.formClass = UserForm
        
    def create_entity(self, parent):
        return model.create_user()

    def load_entities(self, parent):
        return model.list_users()
        
    def get_fields(self, form):
        return (form._fields['name'], po_number, state)

class UserView(views.EntityView):
    def __init__(self):
        self.formClass = UserForm
        self.actions = []
        
    def get_fields(self, form):
        return form._fields.values()
        
    def title(self, entity):
        return "User"

    def get_links(self, entity):
        return ""

def add_rules(app):
    app.add_url_rule('/user_list/<db_id>', view_func=UserListView.as_view('view_user_list'))
    app.add_url_rule('/user/<db_id>/', view_func=UserView.as_view('view_user'))
    app.add_url_rule('/user/<db_id>/menu', view_func=views.MenuView.as_view('handle_user_menu'))
