from sqlalchemy import Table, Column, String, Integer
from sqlalchemy.dialects.postgresql import ARRAY

from apiox.core.db import Model, metadata

__all__ = ['cud_data', 'CUDData']

cud_data = Table('cud_data', metadata,
    Column('cud:fk:oak_primary_person_id', Integer, primary_key=True),
    Column('cud:uas:universitycard_mifare_id', String(14), index=True),
    Column('cud:cas:internal_tel', ARRAY(String()), index=True),
    Column('cud:cas:title', String()),
    Column('cud:cas:suffix', String()),
    Column('_nonce', Integer),
)

class CUDData(Model):
    table = cud_data
