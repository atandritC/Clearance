from qdrant_client import models
from collections.abc import Iterable

from clearance.models import User


def build_document_filter(
    user: User,
    granted_document_versions: Iterable[tuple[str, str]] = (),
) -> models.Filter:
    access_conditions = [
        models.FieldCondition(
            key="access_level",
            match=models.MatchValue(value="company"),
        ),
        models.Filter(
            must=[
                models.FieldCondition(
                    key="access_level",
                    match=models.MatchValue(value="department"),
                ),
                models.FieldCondition(
                    key="department",
                    match=models.MatchValue(value=user.department),
                ),
            ]
        ),
    ]
    access_conditions.extend(
        models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id),
                ),
                models.FieldCondition(
                    key="version",
                    match=models.MatchValue(value=version),
                ),
            ]
        )
        for document_id, version in granted_document_versions
    )
    return models.Filter(
        must=[
            models.FieldCondition(
                key="status",
                match=models.MatchValue(value="active"),
            ),
        ],
        should=access_conditions,
    )
