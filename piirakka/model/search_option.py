from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session

from piirakka.model.base import Base


class SearchOption(Base):
    __tablename__ = "search_options"
    key = Column(String, primary_key=True)
    is_enabled = Column(Integer, nullable=False, default=0)

    def to_pydantic(self):
        return SearchOptionPydantic(
            key=self.key,
            is_enabled=self.is_enabled,
        )


def list_search_options(session: Session) -> list[SearchOption]:
    search_option_data = session.query(SearchOption).all()
    return {option.key: bool(option.is_enabled) for option in search_option_data}


def update_search_option(session: Session, key: str, is_enabled: bool) -> SearchOption | None:
    search_option = session.get(SearchOption, key)
    if search_option:
        if is_enabled is not None:
            # cast "true" or "false" into integer
            search_option.is_enabled = int(is_enabled in [True, "true", "1", 1])
        session.commit()
        session.refresh(search_option)
        return search_option
    return None


class SearchOptionPydantic(BaseModel):
    key: str
    is_enabled: bool

    def to_sqlalchemy(self):
        return SearchOption(
            key=self.key,
            is_enabled=self.is_enabled,
        )
