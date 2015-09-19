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
from .db import cud_data


def _get_subjects(f, nonce):
    items = ijson.items(f, 'cudSubjects.item')
    for subject in ijson.items(f, 'cudSubjects.item'):
        attributes = {a.remote: None for a in cud_attributes}
        attributes.update({a['name']: a['value'] for a in subject['attributes']})
        attributes['_nonce'] = nonce
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
    db_url = os.environ['DB_URL']
    engine = create_engine(db_url)

    url = os.environ['CUD_QUERY_URL'] + '?' + urllib.parse.urlencode({
        'q': '{}:*'.format(cud_id.replace(':', r'\:')),
        'fields': ','.join(attr.remote for attr in cud_attributes),
        'format': 'json',
    })

    with tempfile.TemporaryFile() as f:
        try:
            session = aiohttp_negotiate.NegotiateClientSession(negotiate_client_name=os.environ['CUD_USER'])
            response = yield from session.get(url)
            while True:
                chunk = yield from response.content.read(4096)
                if not chunk:
                    break
                f.write(chunk)
        finally:
            response.close()
            session.close()
        f.seek(0)

        nonce = random.randint(0, 100000000)

        for subjects in _split_every(500, _get_subjects(f, nonce)):
            person_ids = set(s[cud_id] for s in subjects)

            cur = engine.execute(select([cud_data]).where(cud_data.c[cud_id].in_(person_ids)))
            existing_person_ids = set(r[0] for r in cur.fetchall())
            missing_person_ids = person_ids - existing_person_ids

            if existing_person_ids:
                engine.execute(cud_data.update()
                                       .where(cud_data.c[cud_id] == bindparam('id'))
                                       .values(_nonce=nonce,
                                               **{a.remote: bindparam(a.local) for a in cud_attributes if a.local != 'id'}),
                               [{cud_attributes_by_remote[k].local: v for k, v in s.items() if k.startswith('_')} for s in subjects if s[cud_id] in existing_person_ids])

            if missing_person_ids:
                print(len([s for s in subjects if s[cud_id] in missing_person_ids]))
                engine.execute(insert(cud_data),
                               [s for s in subjects if s[cud_id] in missing_person_ids])

        engine.execute(cud_data.delete().where(cud_data.c._nonce != nonce))
