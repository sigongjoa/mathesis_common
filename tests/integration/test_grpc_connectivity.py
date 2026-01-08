import pytest
import asyncio
import grpc
from mathesis_core.grpc import common_pb2, common_pb2_grpc
from mathesis_core.grpc.client import GRPCClientPool

# Mock Servicer for testing
class MockMathesisService(common_pb2_grpc.MathesisServiceServicer):
    async def GetConcept(self, request, context):
        return common_pb2.Concept(
            id=request.id,
            title="Test Concept",
            description="Integrated Test Description"
        )

@pytest.fixture
async def grpc_server():
    server = grpc.aio.server()
    common_pb2_grpc.add_MathesisServiceServicer_to_server(MockMathesisService(), server)
    port = server.add_insecure_port('[::]:50051')
    await server.start()
    yield f"localhost:{port}"
    await server.stop(0)

@pytest.mark.asyncio
async def test_grpc_client_pool_integration(grpc_server):
    target = grpc_server
    pool = GRPCClientPool()
    
    # Reset singleton for clean test
    GRPCClientPool._instance = None
    pool = GRPCClientPool()

    # Get channel from pool
    channel = await pool.get_client(target)
    stub = common_pb2_grpc.MathesisServiceStub(channel)
    
    # Execute call
    request = common_pb2.GetConceptRequest(id="concept-123")
    response = await stub.GetConcept(request)
    
    assert response.id == "concept-123"
    assert response.title == "Test Concept"
    
    # Verify pool reuse
    channel2 = await pool.get_client(target)
    assert channel is channel2
    
    await pool.close_all()
