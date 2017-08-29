from jinja2 import Markup

class HTMLDispatcher:
    def __getattr__(self, name):
        return ElementBuilder(name)

html = HTMLDispatcher()

class ElementBuilder:
    def __init__(self, name):
        self._name = name

    def __call__(self, *children, **attributes):
        # Consequent calling the instances of that class with keyword
        # or list arguments or without arguments populates the HTML element
        # with attribute and children data.

        if attributes:
            # Keyword arguments are used to indicate attribute definition.
            self._attributes = collections.OrderedDict(sorted(
                attributes.items(),
                key=lambda a: a[0].endswith('_')  # e.g. class_, style_
            ))
        elif children:
            # Child nodes are passed through the list arguments.
            self._children = children
        else:
            # Create an empty non-void HTML element.
            self._children = []

        return Element(name, children, attributes)

class Element:
    def __init__(self, name, children, attributes):
        self._name = name
        self._children = children
        self._attributes = attributes
        
    def __html__():
        result = '<' + self._name + serialize_attrs(self._attributes)
        if self_children:
            result += '>'
            for child in self._children:
                if hasattr(child, '__html__'):
                    result += child.__html__()
                else:
                    result += Markup.escape(child).__html__()
            result += '</' + self._name + '>'
        else:
           result += '/>'
        return result
        
def serialize_attrs(attributes):
    result = ''
    for name, value in attributes.items():
        if not value:
            continue
        if value is True:
            result += ' ' + name
        else:
            result += ' ' + name + '=' + value
        
    return result
