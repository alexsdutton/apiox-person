import asyncio
from collections import defaultdict

import ldap3

from ..core.handlers import BaseHandler
from ..core import ldap
from ..core.response import JSONResponse

from apiox.person import __version__, app_name
from .schemas import PERSON_LOOKUP_LIST
from aiohttp.web_exceptions import HTTPFound, HTTPForbidden, HTTPNotFound

_ldap_attributes = {
    'oakPrimaryPersonID': {'local': 'id'},
    'cn': {'local': 'title'},
    'givenName': {'local': 'firstName'},
    'sn': {'local': 'lastName'},
    'mail': {'local': 'email'},
    'oakAlternativeMail': {'local': 'allEmail', 'multiple': True},
    'oakUniversityBarcode': {'local': 'card-number', 'scope': '/person/profile/card-number'},
    'oakOxfordSSOUsername': {'local': 'username', 'multipe': True},
    'oakMifareID': {'local': 'mifare-id', 'scope': '/person/profile/mifare-id'},
    'oakOrcidID': {'local': 'orcid-id'},
}

_local_attribute_names = {v['local']: k for k, v in _ldap_attributes.items()}

class IndexHandler(BaseHandler):
    def get(self, request):
        body = {
            'title': 'Person API',
            'version': __version__,
            '_links': {
                'person:self': {
                    'href': request.app.router['person:self'].url(),
                },
                'person:find': {
                    'href': request.app.router['person:detail'].url(parts={'id': '{id}'}),
                    'templated': True,
                },
                'person:lookup': {
                    'href': request.app.router['person:lookup'].url(),
                },
            },
        }
        return JSONResponse(body=body)


class BasePersonHandler(BaseHandler):
    def ldap_person_as_json(self, app, data, scopes):
        if '/person/profile/view' not in scopes:
            return None
        href = app.router['person:detail'].url(parts={'id': data['oakPrimaryPersonID'][0]})
        result = {
            '_links': {'self': {'href': href}}
        }
        for name, values in data.items():
            defn = _ldap_attributes.get(name)
            if defn is not None:
                if defn.get('scope') and defn['scope'] not in scopes:
                    continue
                if defn.get('multiple'):
                    result[defn['local']] = values
                else:
                    result[defn['local']] = values[0]
        return result

class PersonSelfHandler(BasePersonHandler):
    def get(self, request):
        yield from self.require_authentication(request, with_user=True)
        raise HTTPFound(request.app.router['person:detail'].url(parts={'id': str(request.token.user)}))

class PersonDetailHandler(BasePersonHandler):
    def get(self, request):
        yield from self.require_authentication(request)
        person_id = int(request.match_info['id'])
        scopes = yield from request.token.client.get_permissible_scopes_for_user(request.app, person_id)
        try:
            person_data = self.ldap_person_as_json(request.app,
                                                   ldap.get_person(request.app, person_id),
                                                   scopes)
        except ldap.NoSuchLDAPObject:
            raise HTTPNotFound
        if person_data is None:
            raise HTTPNotFound
        
        return JSONResponse(body=person_data)

class PersonLookupHandler(BasePersonHandler):
    def post(self, request):
        yield from self.require_authentication(request)
        body = yield from self.validated_json(request, app_name, PERSON_LOOKUP_LIST)
        filter = []
        queries = {}
        query_count = len(body)
        for i, item in enumerate(body):
            filter.append('({}={})'.format(_local_attribute_names[item['scheme']],
                                           ldap.escape(item['identifier'])))
            queries[(_local_attribute_names[item['scheme']], item['identifier'])] = i
        filter = '(|{})'.format(''.join(filter)) if len(filter) > 1 else filter[0]
        results = ldap.search(request.app,
                              search_base='ou=people,dc=oak,dc=ox,dc=ac,dc=uk',
                              search_filter=filter,
                              search_scope=ldap3.SUBTREE,
                              attributes=list(_local_attribute_names.values()))
        user_ids = set(ldap.parse_person_dn(r['dn']) for r in results)
        scopes = yield from request.token.client.get_permissible_scopes_for_users(request.app, user_ids)

        finds = {}
        for result in results:
            user_scopes = scopes.get(ldap.parse_person_dn(result['dn']), ())
            item = self.ldap_person_as_json(request.app, result['attributes'],
                                            user_scopes) or {}
            for name, values in result['attributes'].items():
                if _ldap_attributes[name].get('scope') and _ldap_attributes[name]['scope'] not in user_scopes:
                    continue
                for value in values:
                    find = queries.get((name, value))
                    if find is not None:
                        finds[find] = item

        body = {'_links': {'self': {'href': request.app.router['person:lookup'].url()},
                           'item': []}}
        for i in range(query_count):
            if i in finds:
                body['_links']['item'].append(finds[i])
            else:
                body['_links']['item'].append({})
        return JSONResponse(body=body)
