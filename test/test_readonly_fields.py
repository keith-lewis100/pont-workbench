import unittest
import readonly_fields
from google.appengine.ext import ndb

datastore = {}

class Key:
  def __init__(self, id, parent_key):
    self.id = id
    self.parent_key = parent_key

  def get(self):
    return datastore.get(self.id)

  def parent(self):
    return self.parent_key

class Entity:
  def __init__(self, id, parent_key=None):
      self.key = Key(id, parent_key)
      datastore[id] = self

class TestReadOnlyFields(unittest.TestCase):
  def test_simple_render_value(self):
      field = readonly_fields.ReadOnlyField('field_name')
      entity = ndb.Model()
      entity.field_name = 'value'
      self.assertEqual('value', field.render_value(entity));

  def test_simple_accessor(self):
      accessor = readonly_fields.create_accessor(['a'])
      entity = ndb.Model()
      entity.a = 'value'
      self.assertEqual('value', accessor(entity));

  def test_compound_accessor(self):
      accessor = readonly_fields.create_accessor(['a', 'b'])
      entity1 = ndb.Model()
      entity2 = ndb.Model()
      entity2.b = 'value'
      entity1.a = entity2.key
      entity1.put()
      entity2.put()
      self.assertEqual('value', accessor(entity1));

  def test_parent_accessor(self):
      accessor = readonly_fields.create_accessor(['^', 'a'])
      entity1 = Entity('X', Key('parent', None))
      parent = ndb.Model()
      entity = ndb.Model(parent=parent.key)
      parent.a = 'value'
      entity.put()
      parent.put()
      self.assertEqual('value', accessor(entity));

if __name__ == '__main__':
   unittest.main()
