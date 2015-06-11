import os

from aiohttp.web_urldispatcher import UrlDispatcher

from . import __version__, handlers

prefix = 'person'
url_prefix = '/{}/'.format(prefix)

def hook_in(app):
    app['definitions'][prefix] = {'title': 'Person API',
                                  'version': __version__}

    app.router.add_route('GET', url_prefix,
                         handlers.IndexHandler().get,
                         name='person:index')
    app.router.add_route('GET', url_prefix + 'self',
                         handlers.PersonSelfHandler().get,
                         name='person:self')
    app.router.add_route('GET', url_prefix + '{id:\d+}',
                         handlers.PersonDetailHandler().get,
                         name='person:detail')
    app['scopes'].add(name='/person/profile/view',
                      title='View profile',
                      description='Grants access to your name, email address, affiliations and phone number.',
                      available_to_user=True)