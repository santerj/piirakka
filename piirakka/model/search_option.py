from typing import Optional

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

def update_search_option(session: Session, key: str, is_enabled: Optional[bool]) -> Optional[SearchOption]:
    search_option = session.get(SearchOption, key)
    if search_option:
        if is_enabled is not None:
            search_option.is_enabled = is_enabled
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
