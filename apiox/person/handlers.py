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

class PersonSelfHandler(BaseHandler):
    def get(self, request):
        yield from self.require_authentication(request, with_user=True)
        raise HTTPFound(request.app.router['person:detail'].url(parts={'id': str(request.token.user)}))

class PersonDetailHandler(BaseHandler):
    def authorize_request(self, request, person_id):
        if person_id == request.token.user and '/person/profile/view' in request.token.scopes:
            return
        raise HTTPForbidden

    def get(self, request):
        yield from self.require_authentication(request)
        person_id = int(request.match_info['id'])
        self.authorize_request(request, person_id)

        person_data = ldap.get_person(request.app, person_id)
        
        return JSONResponse(body=person_data)
