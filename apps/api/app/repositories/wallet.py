"""
Repository for Wallet entity with blockchain integration.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BlockchainError,
    BusinessRuleViolation,
    NotFoundError,
)
from app.core.logging import log_execution, logger
from app.core.monitoring import track_performance
from app.models.generated import (
    BlockchainTransaction,
    BlockchainTxStatus,
    Wallet,
    WalletType as SQLAlchemyWalletType,
)
from app.repositories.base import BaseRepository
from app.schemas.wallet import (
    GasEstimate,
    SmartWalletDeployment,
    TransactionRequest,
    WalletBalance,
    WalletCreate,
    WalletStats,
    WalletTransaction,
    WalletUpdate,
)


class WalletRepository(BaseRepository[Wallet, WalletCreate, WalletUpdate]):
    """Repository for managing wallets with blockchain integration."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(Wallet)
    
    @property
    def _organization_id_field(self) -> Optional[str]:
        """Field name for organization ID."""
        return "organization_id"
    
    async def get_by_address(
        self,
        db: AsyncSession,
        *,
        address: str,
        chain_id: int,
        load_options: Optional[List[Any]] = None
    ) -> Optional[Wallet]:
        """Get wallet by address and chain ID.
        
        Args:
            db: Database session
            address: Wallet address
            chain_id: Blockchain chain ID
            load_options: SQLAlchemy load options
            
        Returns:
            Wallet or None if not found
        """
        query = select(Wallet).where(
            and_(
                func.lower(Wallet.address) == address.lower(),
                Wallet.chain_id == chain_id
            )
        )
        
        if load_options:
            for option in load_options:
                query = query.options(option)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        chain_id: Optional[int] = None,
        wallet_type: Optional[SQLAlchemyWalletType] = None,
        is_active: bool = True
    ) -> List[Wallet]:
        """Get wallets by user.
        
        Args:
            db: Database session
            user_id: User ID
            chain_id: Optional chain ID filter
            wallet_type: Optional wallet type filter
            is_active: Filter by active status
            
        Returns:
            List of wallets
        """
        query = select(Wallet).where(
            and_(
                Wallet.user_id == user_id,
                Wallet.is_active == is_active
            )
        )
        
        if chain_id is not None:
            query = query.where(Wallet.chain_id == chain_id)
        
        if wallet_type is not None:
            query = query.where(Wallet.type == wallet_type)
        
        query = query.order_by(Wallet.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_organization(
        self,
        db: AsyncSession,
        *,
        organization_id: str,
        chain_id: Optional[int] = None,
        wallet_type: Optional[SQLAlchemyWalletType] = None,
        is_active: bool = True
    ) -> List[Wallet]:
        """Get wallets by organization.
        
        Args:
            db: Database session
            organization_id: Organization ID
            chain_id: Optional chain ID filter
            wallet_type: Optional wallet type filter
            is_active: Filter by active status
            
        Returns:
            List of wallets
        """
        query = select(Wallet).where(
            and_(
                Wallet.organization_id == organization_id,
                Wallet.is_active == is_active
            )
        )
        
        if chain_id is not None:
            query = query.where(Wallet.chain_id == chain_id)
        
        if wallet_type is not None:
            query = query.where(Wallet.type == wallet_type)
        
        query = query.order_by(Wallet.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def validate_wallet_ownership(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> bool:
        """Validate wallet ownership.
        
        Args:
            db: Database session
            wallet_id: Wallet ID
            user_id: User ID to check
            organization_id: Organization ID to check
            
        Returns:
            True if wallet belongs to user or organization
        """
        wallet = await self.get(db, id=wallet_id)
        if not wallet:
            return False
        
        if user_id and wallet.user_id == user_id:
            return True
        
        if organization_id and wallet.organization_id == organization_id:
            return True
        
        return False
    
    async def check_blocklist(
        self,
        db: AsyncSession,
        *,
        address: str,
        chain_id: int
    ) -> bool:
        """Check if address is blocklisted.
        
        Args:
            db: Database session
            address: Wallet address
            chain_id: Chain ID
            
        Returns:
            True if blocklisted
        """
        query = select(func.count()).select_from(Wallet).where(
            and_(
                func.lower(Wallet.address) == address.lower(),
                Wallet.chain_id == chain_id,
                Wallet.blocklist == True
            )
        )
        
        result = await db.execute(query)
        count = result.scalar_one()
        return count > 0
    
    async def check_allowlist(
        self,
        db: AsyncSession,
        *,
        address: str,
        chain_id: int
    ) -> bool:
        """Check if address is allowlisted.
        
        Args:
            db: Database session
            address: Wallet address
            chain_id: Chain ID
            
        Returns:
            True if allowlisted
        """
        query = select(func.count()).select_from(Wallet).where(
            and_(
                func.lower(Wallet.address) == address.lower(),
                Wallet.chain_id == chain_id,
                Wallet.allowlist == True
            )
        )
        
        result = await db.execute(query)
        count = result.scalar_one()
        return count > 0
    
    @track_performance("wallet_balance_fetch")
    async def get_wallet_balance(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
        include_tokens: bool = True,
        calculate_usd: bool = False
    ) -> WalletBalance:
        """Get wallet balance from blockchain.
        
        Args:
            db: Database session
            wallet_id: Wallet ID
            include_tokens: Include token balances
            calculate_usd: Calculate USD values
            
        Returns:
            Wallet balance information
            
        Raises:
            NotFoundError: If wallet not found
            BlockchainError: If blockchain query fails
        """
        wallet = await self.get_or_404(db, id=wallet_id)
        
        # TODO: Integrate with actual blockchain provider
        # This is a placeholder implementation
        logger.info(
            "fetching_wallet_balance",
            wallet_id=wallet_id,
            address=wallet.address,
            chain_id=wallet.chain_id
        )
        
        # Mock balance for now
        balance = WalletBalance(
            wallet_id=wallet_id,
            address=wallet.address,
            chain_id=wallet.chain_id,
            native_balance=Decimal("1.5"),
            native_currency="ETH",
            token_balances=[],
            total_usd_value=Decimal("3000.00") if calculate_usd else None,
            last_updated=datetime.utcnow()
        )
        
        return balance
    
    @track_performance("wallet_transactions_fetch")
    async def get_wallet_transactions(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
        limit: int = 50,
        offset: int = 0,
        include_pending: bool = True
    ) -> List[WalletTransaction]:
        """Get wallet transactions from database.
        
        Args:
            db: Database session
            wallet_id: Wallet ID
            limit: Maximum number of transactions
            offset: Number of transactions to skip
            include_pending: Include pending transactions
            
        Returns:
            List of wallet transactions
        """
        wallet = await self.get_or_404(db, id=wallet_id)
        
        query = select(BlockchainTransaction).where(
            BlockchainTransaction.wallet_id == wallet_id
        )
        
        if not include_pending:
            query = query.where(
                BlockchainTransaction.status != BlockchainTxStatus.PENDING
            )
        
        query = query.order_by(BlockchainTransaction.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        # Convert to WalletTransaction schema
        wallet_txs = []
        for tx in transactions:
            wallet_tx = WalletTransaction(
                hash=tx.hash,
                chain_id=tx.chain_id,
                from_address=tx.from_address,
                to_address=tx.to_address,
                value=tx.value,
                status=tx.status.value,
                block_number=tx.block_number,
                timestamp=tx.mined_at,
                gas_used=None,  # Would need to fetch from receipt
                gas_price=tx.gas_price,
                transaction_fee=None  # Would need to calculate
            )
            wallet_txs.append(wallet_tx)
        
        return wallet_txs
    
    async def estimate_gas(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
        transaction: TransactionRequest
    ) -> GasEstimate:
        """Estimate gas for a transaction.
        
        Args:
            db: Database session
            wallet_id: Wallet ID
            transaction: Transaction request
            
        Returns:
            Gas estimate
            
        Raises:
            NotFoundError: If wallet not found
            BlockchainError: If estimation fails
        """
        wallet = await self.get_or_404(db, id=wallet_id)
        
        # TODO: Integrate with actual blockchain provider
        logger.info(
            "estimating_gas",
            wallet_id=wallet_id,
            to_address=transaction.to_address,
            value=transaction.value
        )
        
        # Mock gas estimate
        gas_estimate = GasEstimate(
            gas_limit="21000",
            gas_price="50000000000",  # 50 Gwei
            max_fee_per_gas="100000000000",  # 100 Gwei
            max_priority_fee_per_gas="2000000000",  # 2 Gwei
            estimated_fee="2100000000000000",  # 0.0021 ETH
            estimated_fee_usd=Decimal("4.20")
        )
        
        return gas_estimate
    
    async def send_transaction(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
        transaction: TransactionRequest,
        payment_order_id: Optional[str] = None
    ) -> BlockchainTransaction:
        """Send a blockchain transaction.
        
        Args:
            db: Database session
            wallet_id: Wallet ID
            transaction: Transaction request
            payment_order_id: Optional payment order ID
            
        Returns:
            Created blockchain transaction
            
        Raises:
            NotFoundError: If wallet not found
            BusinessRuleViolation: If wallet is not active or blocklisted
            BlockchainError: If transaction fails
        """
        wallet = await self.get_or_404(db, id=wallet_id)
        
        # Validate wallet status
        if not wallet.is_active:
            raise BusinessRuleViolation(
                message="Cannot send transaction from inactive wallet",
                rule="wallet_active_required"
            )
        
        if wallet.blocklist:
            raise BusinessRuleViolation(
                message="Cannot send transaction from blocklisted wallet",
                rule="wallet_not_blocklisted"
            )
        
        # Check if recipient is blocklisted
        if await self.check_blocklist(
            db,
            address=transaction.to_address,
            chain_id=wallet.chain_id
        ):
            raise BusinessRuleViolation(
                message="Cannot send transaction to blocklisted address",
                rule="recipient_not_blocklisted"
            )
        
        # TODO: Integrate with actual blockchain provider
        logger.info(
            "sending_transaction",
            wallet_id=wallet_id,
            from_address=wallet.address,
            to_address=transaction.to_address,
            value=transaction.value
        )
        
        # Create transaction record
        tx_data = {
            "hash": f"0x{'0' * 64}",  # Mock hash
            "chain_id": wallet.chain_id,
            "from_address": wallet.address,
            "to_address": transaction.to_address,
            "value": transaction.value,
            "data": transaction.data,
            "gas_limit": transaction.gas_limit or "21000",
            "gas_price": transaction.gas_price or "50000000000",
            "nonce": transaction.nonce,
            "status": BlockchainTxStatus.PENDING,
            "wallet_id": wallet_id,
            "payment_order_id": payment_order_id
        }
        
        blockchain_tx = BlockchainTransaction(**tx_data)
        db.add(blockchain_tx)
        await db.flush()
        
        return blockchain_tx
    
    async def get_wallet_stats(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
        days: int = 30
    ) -> WalletStats:
        """Get wallet statistics.
        
        Args:
            db: Database session
            wallet_id: Wallet ID
            days: Number of days to include in stats
            
        Returns:
            Wallet statistics
        """
        wallet = await self.get_or_404(db, id=wallet_id)
        
        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get transaction stats
        query = select(
            func.count(BlockchainTransaction.id).label("total_transactions"),
            func.sum(
                func.cast(BlockchainTransaction.value, Decimal)
            ).filter(
                BlockchainTransaction.from_address == wallet.address
            ).label("total_sent"),
            func.sum(
                func.cast(BlockchainTransaction.value, Decimal)
            ).filter(
                BlockchainTransaction.to_address == wallet.address
            ).label("total_received"),
            func.count(
                func.distinct(
                    func.case(
                        (BlockchainTransaction.from_address == wallet.address, BlockchainTransaction.to_address),
                        else_=BlockchainTransaction.from_address
                    )
                )
            ).label("unique_interactions"),
            func.min(BlockchainTransaction.created_at).label("first_transaction"),
            func.max(BlockchainTransaction.created_at).label("last_transaction")
        ).select_from(BlockchainTransaction).where(
            and_(
                or_(
                    BlockchainTransaction.from_address == wallet.address,
                    BlockchainTransaction.to_address == wallet.address
                ),
                BlockchainTransaction.created_at >= start_date,
                BlockchainTransaction.status.in_([
                    BlockchainTxStatus.MINED,
                    BlockchainTxStatus.CONFIRMED
                ])
            )
        )
        
        result = await db.execute(query)
        stats_row = result.one()
        
        # Get active chains
        chains_query = select(
            func.distinct(BlockchainTransaction.chain_id)
        ).select_from(BlockchainTransaction).where(
            and_(
                BlockchainTransaction.wallet_id == wallet_id,
                BlockchainTransaction.created_at >= start_date
            )
        )
        
        chains_result = await db.execute(chains_query)
        active_chains = [chain for (chain,) in chains_result.all()]
        
        stats = WalletStats(
            wallet_id=wallet_id,
            total_transactions=stats_row.total_transactions or 0,
            total_received=stats_row.total_received or Decimal("0"),
            total_sent=stats_row.total_sent or Decimal("0"),
            unique_interactions=stats_row.unique_interactions or 0,
            first_transaction=stats_row.first_transaction,
            last_transaction=stats_row.last_transaction,
            active_chains=active_chains
        )
        
        return stats
    
    async def deploy_smart_wallet(
        self,
        db: AsyncSession,
        *,
        deployment: SmartWalletDeployment,
        chain_id: int,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Wallet:
        """Deploy a smart wallet.
        
        Args:
            db: Database session
            deployment: Smart wallet deployment config
            chain_id: Chain ID
            user_id: Optional user ID
            organization_id: Optional organization ID
            
        Returns:
            Created wallet record
            
        Raises:
            BlockchainError: If deployment fails
        """
        # TODO: Integrate with actual smart wallet factory
        logger.info(
            "deploying_smart_wallet",
            factory_address=deployment.factory_address,
            owner_address=deployment.owner_address,
            chain_id=chain_id
        )
        
        # Calculate deterministic address
        # In real implementation, this would use CREATE2 calculation
        computed_address = f"0x{'a' * 40}"
        
        # Create wallet record
        wallet_data = WalletCreate(
            address=computed_address,
            chain_id=chain_id,
            type=SQLAlchemyWalletType.SMART_WALLET,
            smart_wallet_factory=deployment.factory_address,
            smart_wallet_config={
                "owner": deployment.owner_address,
                "salt": deployment.salt,
                "deployed_at": datetime.utcnow().isoformat()
            },
            user_id=user_id,
            organization_id=organization_id
        )
        
        wallet = await self.create(db, obj_in=wallet_data)
        
        return wallet
    
    async def update_wallet_allowlist(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
        allowlist: bool,
        reason: Optional[str] = None
    ) -> Wallet:
        """Update wallet allowlist status.
        
        Args:
            db: Database session
            wallet_id: Wallet ID
            allowlist: New allowlist status
            reason: Optional reason for change
            
        Returns:
            Updated wallet
        """
        wallet = await self.get_or_404(db, id=wallet_id)
        
        if wallet.blocklist and allowlist:
            raise BusinessRuleViolation(
                message="Cannot allowlist a blocklisted wallet",
                rule="blocklist_allowlist_exclusive"
            )
        
        wallet_update = WalletUpdate(allowlist=allowlist)
        wallet = await self.update(db, db_obj=wallet, obj_in=wallet_update)
        
        logger.info(
            "wallet_allowlist_updated",
            wallet_id=wallet_id,
            address=wallet.address,
            allowlist=allowlist,
            reason=reason
        )
        
        return wallet
    
    async def update_wallet_blocklist(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
        blocklist: bool,
        reason: Optional[str] = None
    ) -> Wallet:
        """Update wallet blocklist status.
        
        Args:
            db: Database session
            wallet_id: Wallet ID
            blocklist: New blocklist status
            reason: Optional reason for change
            
        Returns:
            Updated wallet
        """
        wallet = await self.get_or_404(db, id=wallet_id)
        
        if wallet.allowlist and blocklist:
            raise BusinessRuleViolation(
                message="Cannot blocklist an allowlisted wallet",
                rule="blocklist_allowlist_exclusive"
            )
        
        wallet_update = WalletUpdate(blocklist=blocklist)
        wallet = await self.update(db, db_obj=wallet, obj_in=wallet_update)
        
        logger.info(
            "wallet_blocklist_updated",
            wallet_id=wallet_id,
            address=wallet.address,
            blocklist=blocklist,
            reason=reason
        )
        
        return wallet 