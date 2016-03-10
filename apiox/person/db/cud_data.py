from sqlalchemy import Table, Column, String, Integer
from sqlalchemy.dialects.postgresql import ARRAY

from apiox.core.db import Base

__all__ = ['CUDData']


class CUDData(Base):
    __tablename__ = 'cud_data'

    id = Column('cud:fk:oak_primary_person_id', Integer, primary_key=True)
    universitycard_mifare_id = Column('cud:uas:universitycard_mifare_id', String(14), index=True)
    internal_tel = Column('cud:cas:internal_tel', ARRAY(String), index=True)
    title = Column('cud:cas:title', String)
    suffix = Column('cud:cas:suffix', String)
    _nonce = Column(Integer)

CUDData.column_mapping = {
    column.name: CUDData.__mapper__.get_property_by_column(column).key
    for column in list(CUDData.__table__.columns)
}