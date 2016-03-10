import asyncio
from apiox.core.db import API

__version__ = '0.1'

api_id = 'person'

url_prefix = '/{}/'.format(api_id)

@asyncio.coroutine
def setup(app):
    from .schemas import schemas
    from . import handlers

    app['schemas'][api_id] = schemas

    app.router.add_route('*', url_prefix,
                         handlers.IndexHandler(),
                         name='person:index')
    app.router.add_route('*', url_prefix + 'self',
                         handlers.PersonSelfHandler(),
                         name='person:self')
    app.router.add_route('*', url_prefix + '{id:[0-9]+}',
                         handlers.PersonDetailHandler(),
                         name='person:detail')
    app.router.add_route('*', url_prefix + 'lookup',
                         handlers.PersonLookupHandler(),
                         name='person:lookup')

    from . import command
    app['commands']['load_cud_data'] = command.load_cud_data


def declare_api(session):
    session.merge(API.from_json({
        'id': api_id,
        'title': 'Person API',
        'description': 'Provides metadata about people, and allows lookup based on identifiers.',
        'version': __version__,
        'advertise': True,
        'scopes': [{
            'id': '/person/profile/view',
            'title': 'View profile',
            'description': 'Grants access to your name and email address',
            'grantedToUser': True,
        }, {
            'id': '/person/profile/barcode',
            'title': 'View University card barcode',
            'description': 'Grants access to view the barcode on your University card.',
            'grantedToUser': True,
        }, {
            'id': '/person/profile/mifare-id',
            'title': 'View University card Mifare ID',
            'description': 'Grants access to view the Mifare (NFC) ID of your University card.',
            'grantedToUser': True,
        }, {
            'id': '/person/profile/username',
            'title': 'View SSO username',
            'description': 'Grants access to view your Single Sign-On username',
            'grantedToUser': True,
        }, {
            'id': '/person/profile/telephone',
            'title': 'View telephone number',
            'description': 'Grants access to view your telephone number (internal and external)',
            'grantedToUser': True,
        }]
    }))
