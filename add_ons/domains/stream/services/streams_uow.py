"""Unit of Work for stream domain - coordinates transactions across repositories"""
from typing import Optional
from core.utils.logger import get_logger

logger = get_logger(__name__)


class StreamUnitOfWork:
    """
    Coordinates transactions across multiple repositories
    Ensures atomicity - all succeed or all rollback
    """
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self._committed = False
        
        # Repositories (lazy-loaded)
        self._stream_repo = None
        self._membership_repo = None
        self._purchase_repo = None
    
    async def __aenter__(self):
        """Start transaction"""
        if self.db_session:
            await self.db_session.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction"""
        if exc_type is not None:
            await self.rollback()
            return False
        
        if not self._committed:
            await self.commit()
        
        return True
    
    @property
    def stream_repo(self):
        """Get stream repository"""
        if self._stream_repo is None:
            from add_ons.domains.stream.repositories.stream_repository import StreamRepository
            self._stream_repo = StreamRepository(self.db_session)
        return self._stream_repo
    
    @property
    def membership_repo(self):
        """Get membership repository"""
        if self._membership_repo is None:
            from add_ons.domains.stream.repositories.membership_repository import MembershipRepository
            self._membership_repo = MembershipRepository(self.db_session)
        return self._membership_repo
    
    @property
    def purchase_repo(self):
        """Get purchase repository"""
        if self._purchase_repo is None:
            from add_ons.domains.stream.repositories.purchase_repository import PurchaseRepository
            self._purchase_repo = PurchaseRepository(self.db_session)
        return self._purchase_repo
    
    async def commit(self):
        """Commit all changes"""
        if self.db_session:
            await self.db_session.commit()
            self._committed = True
            logger.debug("Transaction committed")
    
    async def rollback(self):
        """Rollback all changes"""
        if self.db_session:
            await self.db_session.rollback()
            logger.warning("Transaction rolled back")