import unittest
import readonly_fields
from google.appengine.ext import ndb
from flask import Flask

class TestReadOnlyFields(unittest.TestCase):
  def test_simple_render_value(self):
      field = readonly_fields.ReadOnlyField('field_name')
      entity = ndb.Model()
      entity.field_name = 'value'
      self.assertEqual('value', field.render_value(entity));

  def test_keyfield_render(self):
      field = readonly_fields.ReadOnlyKeyField('field_name')
      entity = ndb.Model()
      ref_entity = ndb.Model()
      ref_entity.name = 'fred'
      ref_entity.put()
      entity.field_name = ref_entity.key
      app = Flask(__name__)
      app.add_url_rule('/e/<db_id>', 'view_kind')
      with app.test_request_context('/', method='GET'):
        html = field.render(entity)
      self.assertEqual('<a href="/e/%s">fred</a>' % ref_entity.key.urlsafe(), html[1].__html__())

  def test_simple_accessor(self):
      accessor = readonly_fields.create_accessor('a')
      entity = ndb.Model()
      entity.a = 'value'
      self.assertEqual('value', accessor(entity));

  def test_compound_accessor(self):
      accessor = readonly_fields.create_accessor('a.b')
      entity1 = ndb.Model()
      entity2 = ndb.Model()
      entity2.b = 'value'
      entity1.a = entity2.key
      entity1.put()
      entity2.put()
      self.assertEqual('value', accessor(entity1));

  def test_parent_accessor(self):
      accessor = readonly_fields.create_accessor('^.a')
      parent = ndb.Model()
      entity = ndb.Model(parent=parent.key)
      parent.a = 'value'
      entity.put()
      parent.put()
      self.assertEqual('value', accessor(entity));

  def test_structured_property_accessor(self):
      accessor = readonly_fields.create_accessor('key.a')
      struct = ndb.Model()
      outer = ndb.Model()
      outer.a = 'value'
      outer.put()
      struct.key = outer.key
      self.assertEqual('value', accessor(struct));

if __name__ == '__main__':
   unittest.main()
