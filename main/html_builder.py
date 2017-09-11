from cgi import escape

class HTMLDispatcher:
    def __getattr__(self, name):
        return ElementBuilder(name)

html = HTMLDispatcher()

class ElementBuilder:
    def __init__(self, name):
        self._name = name

    def __call__(self, *children, **attributes):
        attrs = {}
        for k, v in attributes.items():
            if k in ('class_', 'class__', 'for_'):
                k = k[:-1]
            elif k.startswith('data_'):
                k = k.replace('_', '-')
            attrs[k] = v

        return Element(self._name, children, attrs)

def render_item(item):
    if hasattr(item, '__html__'):
        return item.__html__()
        
    if hasattr(item, '__iter__'):
        result = ""
        for child in item:
            result += render_item(child)
        return result
        
    return escape(item, quote=False)
    
class Element:
    def __init__(self, name, children, attributes):
        self._name = name
        self._children = children
        self._attributes = attributes
        
    def __html__(self):
        result = '<' + self._name + serialize_attrs(self._attributes)
        if self._children:
            result += '>'
            for child in self._children:
                result += render_item(child)
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
            result += ' %s="%s"'% (name, escape(value, quote=True))
        
    return result
