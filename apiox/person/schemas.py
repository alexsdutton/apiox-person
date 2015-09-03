from .attributes import attributes

PERSON = 'person'
PERSON_LIST = 'person-list'

_person_schema = {
    'type': 'object',
    'properties': {
        a.local: {
            'type': 'string',
        } for a in attributes
    }
}

_person_list_schema = {
    'type': 'array',
    'items': _person_schema,
}

schemas = {
    PERSON: _person_schema,
    PERSON_LIST: _person_list_schema,
}
