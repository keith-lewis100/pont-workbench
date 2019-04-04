import unittest

import properties

class Entity:
    pass

class Field:
    def __init__(self):
        self.label = 'label'
        self.coerce = int
        self.choices = [('1', 'opt1'), ('2', 'opt2')]

class TestProperties(unittest.TestCase):
    def test_select(self):
        obj = Entity()
        obj.opt = 2
        options = enumerate(['opt1', 'opt2'], 1)
        select = properties.SelectProperty('opt', 'label', options)
        val = select.str_for(obj, False)
        self.assertEquals('opt2', val)

    def test_create_property(self):
        select = properties.create_readonly_field('opt', Field())
        obj = Entity()
        obj.opt = 2
        val = select.str_for(obj, False)
        self.assertEquals('opt2', val)
        
if __name__ == '__main__':
   unittest.main()
