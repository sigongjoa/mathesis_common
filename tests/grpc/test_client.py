import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from mathesis_core.grpc.client import GRPCClientPool

@pytest.fixture(autouse=True)
def reset_pool():
    # Reset singleton state before each test
    GRPCClientPool._instance = None
    yield

@pytest.fixture
def mock_grpc_channel():
    with patch("grpc.aio.insecure_channel") as mock:
        yield mock

@pytest.mark.asyncio
async def test_pool_get_client_reuse(mock_grpc_channel):
    pool = GRPCClientPool()
    
    # Get client for same target twice
    client1 = await pool.get_client("localhost:50051")
    client2 = await pool.get_client("localhost:50051")
    
    assert client1 is client2
    assert mock_grpc_channel.call_count == 1

@pytest.mark.asyncio
async def test_pool_get_different_targets(mock_grpc_channel):
    pool = GRPCClientPool()
    
    await pool.get_client("localhost:50051")
    await pool.get_client("localhost:50052")
    
    assert mock_grpc_channel.call_count == 2

@pytest.mark.asyncio
async def test_pool_close_all(mock_grpc_channel):
    pool = GRPCClientPool()
    mock_channel = MagicMock()
    mock_channel.close = AsyncMock()
    mock_grpc_channel.return_value = mock_channel
    
    await pool.get_client("localhost:50051")
    await pool.close_all()
    
    mock_channel.close.assert_called_once()
