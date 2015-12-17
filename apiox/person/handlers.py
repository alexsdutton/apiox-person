import asyncio
from collections import defaultdict
from functools import reduce

import ldap3
from sqlalchemy.sql.expression import or_

from ..core.handlers import BaseHandler
from ..core import ldap
from ..core.response import JSONResponse

from .db import CUDData, cud_data

from apiox.person import __version__, app_name
from apiox.person.attributes import (
    ldap_attributes, ldap_attributes_by_local, ldap_attributes_by_remote, ldap_id,
    cud_attributes, cud_attributes_by_local, cud_attributes_by_remote, cud_id,
)
from .schemas import PERSON_LIST
from aiohttp.web_exceptions import HTTPFound, HTTPNotFound, HTTPBadRequest

class IndexHandler(BaseHandler):
    @asyncio.coroutine
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
    def person_as_json(self, app, ldap_data, cud_data=None, scopes=()):
        if '/person/profile/view' not in scopes:
            return None
        href = app.router['person:detail'].url(parts={'id': int(ldap_data[ldap_id][0])})
        result = {
            '_links': {'self': {'href': href}}
        }
        for name, values in ldap_data.items():
            attr = ldap_attributes_by_remote.get(name)
            values = [v.decode() if isinstance(v, bytes) else v for v in values]
            if attr is not None:
                if attr.scope and attr.scope not in scopes:
                    continue
                if attr.multiple:
                    result[attr.local] = values
                else:
                    result[attr.local] = values[0]
        if cud_data:
            for attr in cud_attributes:
                if not cud_data[attr.remote] or \
                        (attr.scope and attr.scope not in scopes):
                    continue
                result[attr.local] = cud_data[attr.remote]
        return result


class PersonSelfHandler(BasePersonHandler):
    @asyncio.coroutine
    def get(self, request):
        yield from self.require_authentication(request, with_user=True)
        request.match_info['id'] = str(request.token['user_id'])
        response = yield from request.app.router['person:detail'].handler(request)
        response.headers['Content-Location'] = request.app.router['person:detail'].url(parts={'id': str(request.token['user_id'])})
        return response


class PersonDetailHandler(BasePersonHandler):
    @asyncio.coroutine
    def get(self, request):
        yield from self.require_authentication(request)
        person_id = int(request.match_info['id'])
        scopes = yield from (yield from request.token.client).get_permissible_scopes_for_user(person_id,
                                                                                              token=request.token)
        try:
            if any((not attr.scope or attr.scope in scopes) for attr in cud_attributes if attr.local != 'id'):
                cud_data = yield from CUDData.get(request.app,
                                                  **{cud_attributes_by_local['id'].remote: person_id})
            else:
                cud_data = None
            person_data = self.person_as_json(request.app,
                                              ldap_data=request.app['ldap'].get_person(person_id),
                                              cud_data=cud_data,
                                              scopes=scopes)
        except ldap.NoSuchLDAPObject:
            raise HTTPNotFound
        if person_data is None:
            raise HTTPNotFound
        
        return JSONResponse(body=person_data)

class PersonLookupHandler(BasePersonHandler):
    @asyncio.coroutine
    def get(self, request):
        yield from self.require_authentication(request)
        data = []
        for k, v in request.GET.items():
            data.append({k: v})
        if len(data) > 100:
            raise HTTPBadRequest
        return (yield from self.common(request, data))

    @asyncio.coroutine
    def post(self, request):
        yield from self.require_authentication(request)
        data = yield from self.validated_json(request, app_name, PERSON_LIST)
        return (yield from self.common(request, data))

    @asyncio.coroutine
    def common(self, request, data):
        ldap_filter, cud_filter = [], defaultdict(set)
        queries = {}
        query_count = len(data)
        for i, item in enumerate(data):
            if len(item) != 1:
                raise HTTPBadRequest
            k, v = next(iter(item.items()))
            if isinstance(v, list):
                if len(v) != 1:
                    raise HTTPBadRequest
                v = v[0]
            if k in ldap_attributes_by_local:
                defn = ldap_attributes_by_local[k]
                if not defn.identifier:
                    continue
                ldap_filter.append('({}={})'.format(defn.remote,
                                                ldap.escape(v)))
                queries[(defn.local, v)] = i
            elif k in cud_attributes_by_local:
                defn = cud_attributes_by_local[k]
                if not defn.identifier:
                    continue
                cud_filter[defn.remote].add(v)
                queries[(defn.local, v)] = i

        results = defaultdict(lambda: {'id': None, 'ldap': None, 'cud': None})

        if ldap_filter:
            ldap_filter = '(|{})'.format(''.join(ldap_filter)) if len(ldap_filter) > 1 else ldap_filter[0]
            ldap_results = request.app['ldap'].search(search_base='ou=people,dc=oak,dc=ox,dc=ac,dc=uk',
                                                      search_filter=ldap_filter,
                                                      search_scope=ldap3.SUBTREE,
                                                      attributes=list(a.remote for a in ldap_attributes))
            for ldap_result in ldap_results:
                ldap_result = ldap_result['attributes']
                for name, values in ldap_result.items():
                    attr = ldap_attributes_by_remote[name]
                    if not attr.identifier:
                        continue
                    for value in values:
                        key = (attr.local, value)
                        if key in queries:
                            results[queries[key]].update({'id': int(ldap_result[ldap_id][0]),
                                                          'ldap': ldap_result})

        if cud_filter:
            cud_filter = reduce(or_, (cud_data.c[k].in_(v) for k, v in cud_filter.items()))
            cud_results = yield from CUDData.all(request.app, cud_filter)
            for cud_result in cud_results:
                for name, values in cud_result.items():
                    if name.startswith('_'):
                        continue
                    attr = cud_attributes_by_remote[name]
                    if not attr.identifier:
                        continue
                    if not isinstance(values, list):
                        values = (values,)
                    for value in values:
                        key = (attr.local, value)
                        if key in queries:
                            results[queries[key]].update({'id': cud_result[cud_id],
                                                          'cud': cud_result})

        id_mapping = defaultdict(set)
        for i in results:
            id_mapping[results[i]['id']].add(i)

        missing_ldap = {r['id'] for r in results.values() if not r['ldap']}
        if missing_ldap:
            ldap_filter = ['({}={})'.format(ldap_id, i) for i in missing_ldap]
            ldap_filter = '(|{})'.format(''.join(ldap_filter)) if len(ldap_filter) > 1 else ldap_filter[0]
            ldap_results = request.app['ldap'].search(search_base='ou=people,dc=oak,dc=ox,dc=ac,dc=uk',
                                                      search_filter=ldap_filter,
                                                      search_scope=ldap3.SUBTREE,
                                                      attributes=list(a.remote for a in ldap_attributes))
            for ldap_result in ldap_results:
                ldap_result = ldap_result['attributes']
                for i in id_mapping[int(ldap_result[ldap_id][0])]:
                    results[i]['ldap'] = ldap_result

        missing_cud = {r['id'] for r in results.values() if not r['cud']}
        if missing_cud:
            cud_results = yield from CUDData.all(request.app, cud_data.c[cud_id].in_(missing_cud))
            for cud_result in cud_results:
                for i in id_mapping[cud_result[cud_id]]:
                    results[i]['cud'] = cud_result

        scopes = yield from (yield from request.token.client).get_permissible_scopes_for_users((r['id'] for r in results.values()),
                                                                                               token=request.token)

        body = {
            '_links': {
                'self': {'href': request.app.router['person:lookup'].url()},
            },
            '_embedded': {
                'item': [],
            }
        }
        for query, i in zip(data, range(query_count)):
            item = {
                'query': query,
            }
            result = results.get(i)
            if result:
                result = self.person_as_json(request.app,
                                             result['ldap'], result['cud'],
                                             scopes[result['id']])
                if result:
                    item['result'] = result
            body['_embedded']['item'].append({"_embedded": item})
        return JSONResponse(body=body)
