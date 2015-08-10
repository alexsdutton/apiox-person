import os

from aiohttp.web_urldispatcher import UrlDispatcher

from . import __version__, app_name, handlers, schemas

url_prefix = '/{}/'.format(app_name)

def hook_in(app):
    app['definitions'][app_name] = {'title': 'Person API',
                                    'version': __version__,
                                    'schemas': schemas.schemas}

    app.router.add_route('GET', url_prefix,
                         handlers.IndexHandler().get,
                         name='person:index')
    app.router.add_route('GET', url_prefix + 'self',
                         handlers.PersonSelfHandler().get,
                         name='person:self')
    app.router.add_route('GET', url_prefix + '{id:\d+}',
                         handlers.PersonDetailHandler().get,
                         name='person:detail')
    app.router.add_route('POST', url_prefix + 'lookup',
                         handlers.PersonLookupHandler().post,
                         name='person:lookup')
    app['scopes'].add(name='/person/profile/view',
                      title='View profile',
                      description='Grants access to your name, email address, affiliations and phone number.',
                      available_to_user=True)
    app['scopes'].add(name='/person/profile/card-number',
                      title='View University card barcode',
                      description='Grants access to view the barcode on your University card.',
                      available_to_user=True)
    app['scopes'].add(name='/person/profile/mifare-id',
                      title='View University card Mifare ID',
                      description='Grants access to view the Mifare (NFC) ID of your University card.',
                      available_to_user=True)
