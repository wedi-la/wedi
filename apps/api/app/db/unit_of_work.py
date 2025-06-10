"""
Unit of Work pattern implementation for transaction management.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import db_manager

if TYPE_CHECKING:
    # Import repositories to avoid circular imports
    from app.repositories.agent import AgentRepository
    from app.repositories.customer import CustomerRepository
    from app.repositories.integration_key import IntegrationKeyRepository
    from app.repositories.organization import OrganizationRepository
    from app.repositories.payment_link import PaymentLinkRepository
    from app.repositories.payment_order import PaymentOrderRepository
    from app.repositories.price import PriceRepository
    from app.repositories.product import ProductRepository
    from app.repositories.user import UserRepository
    from app.repositories.wallet import WalletRepository


class UnitOfWork:
    """
    Unit of Work pattern implementation.
    
    Manages database transactions across multiple repositories and ensures
    all operations within a unit of work are committed or rolled back together.
    
    Example usage:
        async with UnitOfWork() as uow:
            user = await uow.users.create(db=uow.session, obj_in=user_data)
            org = await uow.organizations.create(db=uow.session, obj_in=org_data)
            await uow.commit()
    """
    
    def __init__(self, session: Optional[AsyncSession] = None):
        """
        Initialize Unit of Work.
        
        Args:
            session: Optional existing database session to use
        """
        self._session = session
        self._repositories_cache: dict[str, Any] = {}
    
    async def __aenter__(self) -> UnitOfWork:
        """Enter the async context manager."""
        if self._session is None:
            # Create a new session if none provided
            self._session_context = db_manager.session()
            self._session = await self._session_context.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        if hasattr(self, "_session_context"):
            # Let the session context manager handle commit/rollback
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        # Clear repository cache
        self._repositories_cache.clear()
    
    @property
    def session(self) -> AsyncSession:
        """Get the current database session."""
        if self._session is None:
            raise RuntimeError("UnitOfWork must be used within async context manager")
        return self._session
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.session.rollback()
    
    async def flush(self) -> None:
        """Flush pending changes to the database without committing."""
        await self.session.flush()
    
    async def refresh(self, instance: Any) -> None:
        """Refresh an instance from the database."""
        await self.session.refresh(instance)
    
    # Repository properties - lazy loaded
    
    @property
    def users(self) -> UserRepository:
        """Get UserRepository instance."""
        if "users" not in self._repositories_cache:
            from app.repositories.user import UserRepository
            self._repositories_cache["users"] = UserRepository()
        return self._repositories_cache["users"]
    
    @property
    def organizations(self) -> OrganizationRepository:
        """Get OrganizationRepository instance."""
        if "organizations" not in self._repositories_cache:
            from app.repositories.organization import OrganizationRepository
            self._repositories_cache["organizations"] = OrganizationRepository()
        return self._repositories_cache["organizations"]
    
    @property
    def agents(self) -> AgentRepository:
        """Get AgentRepository instance."""
        if "agents" not in self._repositories_cache:
            from app.repositories.agent import AgentRepository
            self._repositories_cache["agents"] = AgentRepository()
        return self._repositories_cache["agents"]
    
    @property
    def payment_links(self) -> PaymentLinkRepository:
        """Get PaymentLinkRepository instance."""
        if "payment_links" not in self._repositories_cache:
            from app.repositories.payment_link import PaymentLinkRepository
            self._repositories_cache["payment_links"] = PaymentLinkRepository()
        return self._repositories_cache["payment_links"]
    
    @property
    def payment_orders(self) -> PaymentOrderRepository:
        """Get PaymentOrderRepository instance."""
        if "payment_orders" not in self._repositories_cache:
            from app.repositories.payment_order import PaymentOrderRepository
            self._repositories_cache["payment_orders"] = PaymentOrderRepository()
        return self._repositories_cache["payment_orders"]
    
    @property
    def customers(self) -> CustomerRepository:
        """Get CustomerRepository instance."""
        if "customers" not in self._repositories_cache:
            from app.repositories.customer import CustomerRepository
            self._repositories_cache["customers"] = CustomerRepository()
        return self._repositories_cache["customers"]
    
    @property
    def products(self) -> ProductRepository:
        """Get ProductRepository instance."""
        if "products" not in self._repositories_cache:
            from app.repositories.product import ProductRepository
            self._repositories_cache["products"] = ProductRepository()
        return self._repositories_cache["products"]
    
    @property
    def prices(self) -> PriceRepository:
        """Get PriceRepository instance."""
        if "prices" not in self._repositories_cache:
            from app.repositories.price import PriceRepository
            self._repositories_cache["prices"] = PriceRepository()
        return self._repositories_cache["prices"]
    
    @property
    def wallets(self) -> WalletRepository:
        """Get WalletRepository instance."""
        if "wallets" not in self._repositories_cache:
            from app.repositories.wallet import WalletRepository
            self._repositories_cache["wallets"] = WalletRepository()
        return self._repositories_cache["wallets"]
    
    @property
    def integration_keys(self) -> IntegrationKeyRepository:
        """Get IntegrationKeyRepository instance."""
        if "integration_keys" not in self._repositories_cache:
            from app.repositories.integration_key import IntegrationKeyRepository
            self._repositories_cache["integration_keys"] = IntegrationKeyRepository()
        return self._repositories_cache["integration_keys"]


# FastAPI dependency
async def get_unit_of_work() -> UnitOfWork:
    """
    FastAPI dependency to get a Unit of Work instance.
    
    Yields:
        UnitOfWork instance
        
    Example:
        @router.post("/users")
        async def create_user(
            user_data: UserCreate,
            uow: UnitOfWork = Depends(get_unit_of_work)
        ):
            async with uow:
                user = await uow.users.create(db=uow.session, obj_in=user_data)
                await uow.commit()
                return user
    """
    return UnitOfWork() 