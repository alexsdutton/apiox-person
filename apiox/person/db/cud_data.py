from sqlalchemy import Table, Column, String, Integer

from apiox.core.db import Model, metadata

__all__ = ['cud_data', 'CUDData']

cud_data = Table('cud_data', metadata,
    Column('cud:fk:oak_primary_person_id', Integer, primary_key=True),
    Column('cud:uas:universitycard_mifare_id', String(14), index=True),
)


class CUDData(Model):
    table = cud_data
