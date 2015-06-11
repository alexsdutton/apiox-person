import asyncio

from ..core.handlers import BaseHandler
from ..core import ldap
from ..core.response import JSONResponse

from apiox.person import __version__
from aiohttp.web_exceptions import HTTPFound, HTTPForbidden

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
            },
        }
        return JSONResponse(body=body)

class BasePersonHandler(BaseHandler):
    def ldap_person_as_json(self, app, data):
        href = app.router['person:detail'].url(parts={'id': data['oakPrimaryPersonID'][0]})
        result = {
            '_links': {'self': {'href': href}}
        }
        if 'cn' in data:
            result['title'] = data['cn'][0]
        if 'givenName' in data:
            result['firstName'] = data['givenName'][0]
        if 'sn' in data:
            result['lastName'] = data['sn'][0]
        if 'mail' in data:
            result['primaryEmail'] = data['mail'][0]
        if 'oakAlternativeMail' in data:
            result['allEmail'] = data['oakAlternativeMail']
        return result

class PersonSelfHandler(BasePersonHandler):
    def get(self, request):
        yield from self.require_authentication(request, with_user=True)
        raise HTTPFound(request.app.router['person:detail'].url(parts={'id': str(request.token.user)}))

class PersonDetailHandler(BasePersonHandler):
    def authorize_request(self, request, person_id):
        if person_id == request.token.user and '/person/profile/view' in request.token.scopes:
            return
        raise HTTPForbidden

    def get(self, request):
        yield from self.require_authentication(request)
        person_id = int(request.match_info['id'])
        self.authorize_request(request, person_id)

        person_data = self.ldap_person_as_json(request.app,
                                               ldap.get_person(request.app, person_id))
        
        return JSONResponse(body=person_data)
