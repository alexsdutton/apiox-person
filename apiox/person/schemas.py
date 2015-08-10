PERSON_LOOKUP_LIST = 'person-lookup-list'

schemas = {
    PERSON_LOOKUP_LIST: {
        'type': 'array',
        'items': {
            'type': 'object',
            'oneOf': [{
                'properties': {
                    'scheme': {'enum': ['card-number']},
                    'identifier': {'type': 'string', 'pattern': '^[0-9]{7}$'},
                }
            }, {
                'properties': {
                    'scheme': {'enum': ['username']},
                    'identifier': {'type': 'string', 'pattern': '^[0-9a-z]{1,8}$'},
                }
            }, {
                'properties': {
                    'scheme': {'enum': ['mifare-id']},
                    'identifier': {'type': 'string', 'pattern': '^[0-9a-f]{14}$'},
                }
            }, {
                'properties': {
                    'scheme': {'enum': ['email']},
                    'identifier': {'type': 'string', 'format': 'email'},
                }
            }, {
                'properties': {
                    'scheme': {'enum': ['orcid-id']},
                    'identifier': {'type': 'string', 'pattern': '^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}$'},
                }
            }],
            'properties': {'scheme': {}, 'identifier': {}},
            'required': ['scheme', 'identifier'],
            'additionalProperties': False,
        },
        "minItems": 1,
        "maxItems": 1000,
        "uniqueItems": True,
    },
}
