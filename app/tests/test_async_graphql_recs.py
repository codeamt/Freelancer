import pytest
from strawberry.test import AsyncGraphQLTestClient
from app.services.recommender_service import schema

@pytest.fixture(scope="session")
def async_gql_client():
    return AsyncGraphQLTestClient(schema)

@pytest.mark.asyncio
async def test_async_recommendations_query(async_gql_client):
    query = """
    query TestRecs($userId: ID!) {
        recommendations(userId: $userId) {
            itemId
            score
        }
    }
    """
    variables = {"userId": "1"}
    result = await async_gql_client.query(query, variables)
    assert "recommendations" in result.data