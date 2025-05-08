from sqlmodel import Field, SQLModel, Column, DateTime, func, select, Session
from datetime import datetime
from typing import Optional
import uuid

class File(SQLModel, table=True):
    __tablename__ = "files"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    file_path: Optional[str] = Field(default=None)
    file_name: str
    authenticated: bool = Field(default=False)
    type: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    def __repr__(self):
        return f"File(id={self.id}, user_id={self.user_id}, file_name={self.file_name},  type={self.type}, created_at={self.created_at}, updated_at={self.updated_at})"