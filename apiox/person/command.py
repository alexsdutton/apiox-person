import asyncio
import csv
import itertools
import os
import random
import tempfile
import urllib

import aiohttp_negotiate
import ijson
from sqlalchemy import create_engine, select, bindparam, insert

from .attributes import cud_id, cud_attributes, cud_attributes_by_remote
from .db import cud_data, CUDData


def _get_subjects(f):
    items = ijson.items(f, 'cudSubjects.item')
    for subject in ijson.items(f, 'cudSubjects.item'):
        attributes = {a.remote: None for a in cud_attributes}
        attributes.update({a['name']: a['value'] for a in subject['attributes']})
        attributes[cud_id] = int(attributes[cud_id])
        yield attributes


def _split_every(n, iterable):
    i = iter(iterable)
    piece = list(itertools.islice(i, n))
    while piece:
        yield piece
        piece = list(itertools.islice(i, n))


@asyncio.coroutine
def load_cud_data(app):
    url = os.environ['CUD_QUERY_URL'] + '?' + urllib.parse.urlencode({
        'q': '{}:*'.format(cud_id.replace(':', r'\:')),
        'fields': ','.join(attr.remote for attr in cud_attributes),
        'format': 'json',
    })

    with tempfile.TemporaryFile() as f:
        session = aiohttp_negotiate.NegotiateClientSession(negotiate_client_name=os.environ['CUD_USER'])
        try:
            response = yield from session.get(url)
            try:
                while True:
                    chunk = yield from response.content.read(4096)
                    if not chunk:
                        break
                    f.write(chunk)
            finally:
                response.close()
        finally:
            session.close()
        f.seek(0)

        nonce = random.randint(0, 100000000)

        with app['db-session']() as session:
            for subjects in _split_every(50, _get_subjects(f)):
                for cud_data in (CUDData(_nonce=nonce,
                                         **{CUDData.column_mapping[k]: v for k, v in subject.items()})
                                 for subject in subjects):
                    session.merge(cud_data)
                session.commit()

            session.query(CUDData).filter(CUDData._nonce != nonce).delete()
