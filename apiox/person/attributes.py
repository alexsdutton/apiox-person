import collections

Attribute = collections.namedtuple('Attribute', 'remote local scope multiple identifier')

ldap_attributes = (
    Attribute('oakPrimaryPersonID', 'id', None, False, True),
    Attribute('cn', 'title', None, False, False),
    Attribute('givenName', 'firstName', None, False, False),
    Attribute('sn', 'lastName', None, False, False),
    Attribute('mail', 'email', None, False, True),
    Attribute('oakAlternativeMail', 'allEmail', None, True, True),
    Attribute('oakUniversityBarcode', 'barcode', '/person/profile/barcode', False, True),
    Attribute('oakUniversityBarcodeFull', 'barcodeFull', '/person/profile/barcode', False, True),
    Attribute('oakOxfordSSOUsername', 'username', '/person/profile/username', True, True),
#    Attribute('oakMifareID', 'mifareId', None, '/person/profile/mifare-id', True),
    Attribute('oakOrcidID', 'orcidId', None, False, True),
)

cud_attributes = (
    Attribute('cud:fk:oak_primary_person_id', 'id', None, False, True),
    Attribute('cud:uas:universitycard_mifare_id', 'mifareId', '/person/profile/mifare-id', False, True),
    Attribute('cud:cas:internal_tel', 'telephoneExtension', '/person/profile/telephone', True, False),
    Attribute('cud:cas:title', 'honorific', None, False, False),
    Attribute('cud:cas:suffix', 'suffix', None, False, False),
)

ldap_attributes_by_local = {a.local: a for a in ldap_attributes}
ldap_attributes_by_remote = {a.remote: a for a in ldap_attributes}

cud_attributes_by_local = {a.local: a for a in cud_attributes}
cud_attributes_by_remote = {a.remote: a for a in cud_attributes}

ldap_id = ldap_attributes_by_local['id'].remote
cud_id = cud_attributes_by_local['id'].remote
