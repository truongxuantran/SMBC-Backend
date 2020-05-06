from typing import Any, Dict, List, Optional, Union

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from ..database import db


class BaseRepository(object):
    model_class = db.Model
    has_uuid = False

    def __init__(self, database: Optional[SQLAlchemy]) -> None:
        self.db = database

    def all(self) -> List[db.Model]:
        return self.model_class.query.all()

    def get(self,
            offset: int,
            limit: int,
            order: Any = None) -> List[db.Model]:
        query = self.model_class.query
        if order is not None:
            query = query.order_by(order)

        return query.offset(offset).limit(limit).all()

    def create(self, fields: Dict) -> db.Model:
        model = self.model_class(**fields)
        self.db.session.add(model)
        self.db.session.commit()
        return model

    def update(self, model: db.Model, fields: Dict) -> db.Model:
        for key in fields:
            setattr(model, key, fields[key])
        self.db.session.add(model)
        self.db.session.commit()
        return model

    def delete(self, model: db.Model) -> bool:
        self.db.session.delete(model)
        self.db.session.commit()
        return True

    def find(self, primary_id: Any) -> db.Model:
        return self.model_class.query.filter_by(id=primary_id).first()

    def exist(self, primary_id: Union[int, str]) -> bool:
        return bool(self.model_class.query.filter_by(id=primary_id).first())

    def get_by_filter(self,
                      filter_dict: Dict = None,
                      offset: int = 0,
                      limit: int = 10,
                      order: str = "id",
                      direction: str = "asc") -> List[db.Model]:
        if filter_dict is None:
            filter_dict = {}
        query = self.model_class.query.order_by(text(order + " " + direction))

        return query.filter_by(**filter_dict).offset(offset).limit(limit).all()

    def count_by_filter(self, filter_dict: Dict = None) -> int:
        if filter_dict is None:
            filter_dict = {}
        query = self.model_class.query

        return query.filter_by(**filter_dict).count()
