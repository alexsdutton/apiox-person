import asyncio
import os
import urllib

import aiohttp_negotiate

from .attributes import cud_id, cud_attributes

@asyncio.coroutine
def load_cud_data(app):
    session = aiohttp_negotiate.NegotiateClientSession(negotiate_client_name=os.environ['CUD_USER'])
    url = os.environ['CUD_QUERY_URL'] + '?' + urllib.parse.urlencode({
        'q': cud_id.replace(':', r'\:')
    })