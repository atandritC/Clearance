from qdrant_client import QdrantClient, models

from clearance.models import User
from clearance.retrieval.filters import build_document_filter


def test_search_filter_allows_only_company_department_and_granted_versions():
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
                models.PointStruct(
                    id=6,
                    vector=[0.5, 0.5],
                    payload={
                        "document_id": "HR-005",
                        "version": "1.0",
                        "department": "People Operations",
                        "access_level": "restricted",
                        "status": "active",
                    },
                ),
                models.PointStruct(
                    id=7,
                    vector=[0.4, 0.6],
                    payload={
                        "document_id": "HR-006",
                        "version": "1.1",
                        "department": "People Operations",
                        "access_level": "restricted",
                        "status": "active",
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

        granted_result = client.query_points(
            collection_name="access-check",
            query=[1.0, 0.0],
            query_filter=build_document_filter(user, {("HR-005", "1.0")}),
            limit=10,
            with_payload=True,
        )

        assert {point.id for point in granted_result.points} == {1, 2, 6}
    finally:
        client.close()
