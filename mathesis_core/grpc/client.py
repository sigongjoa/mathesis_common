import grpc.aio
from typing import Dict, Any, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

class GRPCClientPool:
    """
    Manages a pool of gRPC channels and clients to optimize performance.
    Ensures channels are reused for the same target.
    """
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GRPCClientPool, cls).__new__(cls)
            cls._instance.channels = {}
        return cls._instance

    def __init__(self):
        # Channels dict is initialized in __new__
        pass

    async def get_client(self, target: str) -> grpc.aio.Channel:
        """
        Returns a gRPC channel for the given target.
        Creates it if it doesn't already exist.
        """
        async with self._lock:
            if target not in self.channels:
                logger.info(f"Creating new gRPC channel to {target}")
                channel = grpc.aio.insecure_channel(target)
                self.channels[target] = channel
            
            return self.channels[target]

    async def close_all(self):
        """
        Closes all open gRPC channels.
        """
        async with self._lock:
            for target, channel in self.channels.items():
                logger.info(f"Closing gRPC channel to {target}")
                await channel.close()
            self.channels.clear()

async def get_grpc_pool() -> GRPCClientPool:
    return GRPCClientPool()
