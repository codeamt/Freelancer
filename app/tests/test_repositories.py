# tests/test_repositories.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from add_ons.services.postgres.repository import PostgresRepository

@pytest.fixture
def mock_repo():
    session = AsyncMock()
    model = MagicMock()
    return PostgresRepository(session, model)

@pytest.mark.asyncio
async def test_bulk_operations(mock_repo):
    # Setup mock entity
    mock_entity = MagicMock()
    mock_entity.id = "1"
    
    # Test get_bulk
    mock_repo.session.execute.return_value.scalars.return_value = [mock_entity]
    result = await mock_repo.get_bulk(["1", "2"])
    assert "1" in result
    assert result["1"].id == "1"
    
    # Test save_bulk
    entities = [MagicMock(), MagicMock()]
    saved = await mock_repo.save_bulk(entities)
    assert len(saved) == 2
    mock_repo.session.add_all.assert_called_once_with(entities)