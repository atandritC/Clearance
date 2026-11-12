from qdrant_client import QdrantClient, models

from clearance.models import User
from clearance.retrieval.filters import build_document_filter


def test_search_filter_only_allows_active_company_and_same_department_documents():
    client = QdrantClient(":memory:")

    try:
        client.create_collection(
            collection_name="access-check",
            vectors_config=models.VectorParams(
                size=2,
                distance=models.Distance.COSINE,
            ),
        )
        client.upsert(
            collection_name="access-check",
            points=[
                models.PointStruct(
                    id=1,
                    vector=[1.0, 0.0],
                    payload={
                        "document_id": "CO-001",
                        "department": "Company",
                        "access_level": "company",
                        "status": "active",
                    },
                ),
                models.PointStruct(
                    id=2,
                    vector=[0.9, 0.1],
                    payload={
                        "document_id": "IT-001",
                        "department": "IT Operations",
                        "access_level": "department",
                        "status": "active",
                    },
                ),
                models.PointStruct(
                    id=3,
                    vector=[0.8, 0.2],
                    payload={
                        "document_id": "HR-001",
                        "department": "People Operations",
                        "access_level": "department",
                        "status": "active",
                    },
                ),
                models.PointStruct(
                    id=4,
                    vector=[0.7, 0.3],
                    payload={
                        "document_id": "IT-002",
                        "department": "IT Operations",
                        "access_level": "restricted",
                        "status": "active",
                    },
                ),
                models.PointStruct(
                    id=5,
                    vector=[0.6, 0.4],
                    payload={
                        "document_id": "CO-001",
                        "department": "Company",
                        "access_level": "company",
                        "status": "superseded",
                    },
                ),
            ],
        )

        user = User(
            id=2,
            email="engineer@astervale.example",
            display_name="Demo Engineer",
            role="engineer",
            department="IT Operations",
            is_active=True,
        )

        result = client.query_points(
            collection_name="access-check",
            query=[1.0, 0.0],
            query_filter=build_document_filter(user),
            limit=10,
            with_payload=True,
        )

        assert {point.id for point in result.points} == {1, 2}
    finally:
        client.close()
