import uuid
from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model that every T-Career model inherits.
    Provides UUID primary key and automatic audit timestamps.
    Using UUID prevents enumeration attacks and makes IDs safe to expose in APIs.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"
