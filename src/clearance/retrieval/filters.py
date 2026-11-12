from qdrant_client import models

from clearance.models import User


def build_document_filter(user: User) -> models.Filter:
    return models.Filter(
        must=[
            models.FieldCondition(
                key="status",
                match=models.MatchValue(value="active"),
            ),
        ],
        should=[
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
        ],
    )
