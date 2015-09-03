import collections

Attribute = collections.namedtuple('Attribute', 'remote local scope multiple identifier')

attributes = (
    Attribute('oakPrimaryPersonID', 'id', None, False, True),
    Attribute('cn', 'title', None, False, False),
    Attribute('givenName', 'firstName', None, False, False),
    Attribute('sn', 'lastName', None, False, False),
    Attribute('mail', 'email', None, False, True),
    Attribute('oakAlternativeMail', 'allEmail', None, True, True),
    Attribute('oakUniversityBarcode', 'barcode', '/person/profile/barcode', False, True),
    Attribute('oakUniversityBarcodeFull', 'barcodeFull', '/person/profile/barcode', False, True),
    Attribute('oakOxfordSSOUsername', 'username', None, '/person/profile/username', True),
    Attribute('oakMifareID', 'mifareId', None, '/person/profile/mifare-id', True),
    Attribute('oakOrcidID', 'orcidId', None, False, True),
)

attributes_by_local = {a.local: a for a in attributes}
attributes_by_remote = {a.remote: a for a in attributes}
