"""
Repository for Circle-based wallet integration.
"""
from datetime import datetime
from decimal import Decimal
import uuid
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BlockchainError,
    BusinessRuleViolation,
    ExternalServiceError,
    NotFoundError,
)
from app.core.logging import log_execution, logger
from app.core.monitoring import track_performance
from app.models.generated import (
    Wallet as SQLAlchemyWallet,
    WalletType as SQLAlchemyWalletType,
    BlockchainTransaction,
    BlockchainTxStatus,
)
from app.repositories.base import BaseRepository
from app.repositories.wallet import WalletRepository
from app.schemas.wallet import (
    CircleWallet,
    CircleWalletBalance,
    CircleWalletCreate,
    CircleWalletSet,
    CircleWalletSetCreate,
    CircleWalletTransaction,
    GasEstimate,
    SmartWalletDeployment,
    TransactionRequest,
    WalletBalance,
    WalletCreate,
    WalletStats,
    WalletTransaction,
    WalletUpdate,
)
from app.services.circle_service import circle_service


class CircleWalletRepository(WalletRepository):
    """Repository for Circle-based developer-controlled wallets."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__()
        
    async def create_wallet_set(
        self, 
        db: AsyncSession, 
        *,
        wallet_set: CircleWalletSetCreate,
        organization_id: str,
    ) -> CircleWalletSet:
        """
        Create a new Circle wallet set tied to an organization.
        
        Args:
            db: Database session
            wallet_set: Wallet set data
            organization_id: Organization ID
            
        Returns:
            CircleWalletSet: Created wallet set
        """
        try:
            # Create wallet set in Circle - now returns a dictionary, not SDK model
            circle_wallet_set = await circle_service.create_wallet_set(wallet_set.name)
            
            # Store the wallet set ID in metadata
            # In a real implementation, we would create a dedicated DB table for wallet sets
            # but for now, we'll add metadata to the organization
            
            # Return wallet set info - extract data from dictionary response
            return CircleWalletSet(
                id=circle_wallet_set.get("id"),
                name=circle_wallet_set.get("name"),
                organization_id=organization_id,
                created_at=datetime.utcnow()
            )
        except ExternalServiceError as e:
            logger.error(
                "create_wallet_set_failed",
                error=str(e),
                organization_id=organization_id
            )
            raise
    
    async def create_circle_wallet(
        self,
        db: AsyncSession,
        *,
        wallet_data: CircleWalletCreate,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> CircleWallet:
        """
        Create a new Circle wallet within a wallet set.
        
        Args:
            db: Database session
            wallet_data: Wallet data with wallet_set_id and blockchain
            user_id: Optional user ID
            organization_id: Optional organization ID
            
        Returns:
            CircleWallet: Created wallet
        """
        try:
            # Create metadata to store user/organization association
            metadata = {
                "app_user_id": user_id if user_id else "",
                "app_organization_id": organization_id if organization_id else "",
                "app_created_at": datetime.utcnow().isoformat(),
                "app_environment": "production" if not wallet_data.is_test else "sandbox"
            }
            
            # Create wallet in Circle - now returns a dictionary, not SDK model
            circle_wallet = await circle_service.create_wallet(
                wallet_set_id=wallet_data.wallet_set_id,
                blockchain=wallet_data.blockchain,
                metadata=metadata
            )
            
            # Extract wallet ID from dictionary response
            circle_wallet_id = circle_wallet.get("id")
            if not circle_wallet_id:
                raise ExternalServiceError(
                    message="Failed to get wallet ID from Circle response",
                    service="circle"
                )
            
            # Get addresses for this wallet
            addresses = await circle_service.get_wallet_addresses(
                wallet_id=circle_wallet_id
            )
            
            # Find matching address for this blockchain
            address = None
            for addr in addresses:
                if addr.get("blockchain") == wallet_data.blockchain:
                    address = addr.get("address")
                    break
            
            if not address:
                raise ExternalServiceError(
                    message=f"No address found for blockchain {wallet_data.blockchain}",
                    service="circle"
                )
            
            # Map blockchain to chain_id (this would be expanded in a real implementation)
            chain_id_mapping = {
                "ETH-GOERLI": 5,
                "ETH-SEPOLIA": 11155111,
                "ETH-MAINNET": 1,
                "MATIC-MUMBAI": 80001,
                "MATIC-MAINNET": 137,
                "AVAXC-MAINNET": 43114,
                "AVAXC-TESTNET": 43113,
            }
            
            chain_id = chain_id_mapping.get(wallet_data.blockchain, 0)
            
            # Create new wallet in DB
            wallet = Wallet(
                id=str(uuid.uuid4()),
                address=address,
                chain_id=chain_id,
                type=SQLAlchemyWalletType.CIRCLE,  # Enum value
                user_id=user_id,
                organization_id=organization_id,
                metadata={
                    "circle_wallet_id": circle_wallet_id,
                    "circle_wallet_set_id": wallet_data.wallet_set_id,
                    "blockchain": wallet_data.blockchain,
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
            
            # Create wallet in DB
            wallet = await self.create(db, obj_in=wallet)
            
            # Return wallet with Circle-specific fields
            return CircleWallet(
                id=wallet.id,
                address=address,
                circle_wallet_id=circle_wallet_id,
                circle_wallet_set_id=wallet_data.wallet_set_id,
                blockchain=wallet_data.blockchain,
                chain_id=chain_id,
                user_id=user_id,
                organization_id=organization_id,
                created_at=wallet.created_at
            )
        except ExternalServiceError as e:
            logger.error(
                "create_circle_wallet_failed",
                error=str(e),
                user_id=user_id,
                organization_id=organization_id
            )
            raise
    
    async def get_circle_wallets_by_set(
        self,
        db: AsyncSession,
        *,
        wallet_set_id: str,
    ) -> List[CircleWallet]:
        """
        Get all wallets in a Circle wallet set.
        
        Args:
            db: Database session
            wallet_set_id: Circle wallet set ID
            
        Returns:
            List[CircleWallet]: Wallets in the set
        """
        try:
            # Get wallets from Circle - now returns a list of dictionaries
            wallets_data = await circle_service.get_wallets(wallet_set_id=wallet_set_id)
            
            # Map to schema
            wallets = []
            for wallet_data in wallets_data:
                # Fetch our internal wallet record if it exists
                wallet_query = select(Wallet).where(
                    and_(
                        Wallet.metadata['circle_wallet_id'].astext == wallet_data.get("id"),
                        Wallet.type == SQLAlchemyWalletType.CIRCLE,
                    )
                )
                wallet_result = await db.execute(wallet_query)
                wallet = wallet_result.scalar_one_or_none()

                if wallet:
                    # Extract blockchain from wallet metadata
                    blockchain = wallet.metadata.get("blockchain")
                    
                    # Map to CircleWallet schema
                    wallet_model = CircleWallet(
                        id=wallet.id,
                        address=wallet.address,
                        circle_wallet_id=wallet_data.get("id"),
                        circle_wallet_set_id=wallet_set_id,
                        blockchain=blockchain,
                        chain_id=wallet.chain_id,
                        user_id=wallet.user_id,
                        organization_id=wallet.organization_id,
                        created_at=wallet.created_at,
                    )
                    
                    wallets.append(wallet_model)
            
            return wallets
        except ExternalServiceError as e:
            logger.error(
                "get_circle_wallets_failed",
                error=str(e),
                wallet_set_id=wallet_set_id
            )
            raise
    
    async def get_circle_wallet(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
    ) -> CircleWallet:
        """
        Get Circle wallet details by our DB wallet ID.
        
        Args:
            db: Database session
            wallet_id: Our internal wallet ID
            
        Returns:
            CircleWallet: Wallet details
            
        Raises:
            NotFoundError: If wallet not found
        """
        wallet = await self.get_or_404(db, id=wallet_id)
        
        if wallet.type != SQLAlchemyWalletType.CIRCLE:
            raise NotFoundError(
                message=f"Wallet {wallet_id} is not a Circle wallet",
                entity="wallet"
            )
        
        config = wallet.metadata or {}
        circle_wallet_id = config.get('circle_wallet_id')
        circle_wallet_set_id = config.get('circle_wallet_set_id')
        blockchain = config.get('blockchain')
        
        if not circle_wallet_id or not circle_wallet_set_id:
            raise NotFoundError(
                message=f"Wallet {wallet_id} is missing Circle configuration",
                entity="wallet"
            )
        
        try:
            # Get wallet details from Circle - now returns dictionary
            wallet_data = await circle_service.get_wallet(
                wallet_set_id=circle_wallet_set_id,
                wallet_id=circle_wallet_id
            )
            
            return CircleWallet(
                id=wallet.id,
                address=wallet.address,
                circle_wallet_id=circle_wallet_id,
                circle_wallet_set_id=circle_wallet_set_id,
                blockchain=blockchain,
                chain_id=wallet.chain_id,
                user_id=wallet.user_id,
                organization_id=wallet.organization_id,
                created_at=wallet.created_at
            )
        except ExternalServiceError as e:
            logger.error(
                "get_circle_wallet_failed",
                error=str(e),
                wallet_id=wallet_id
            )
            raise
    
    async def get_circle_wallet_balance(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
    ) -> CircleWalletBalance:
        """
        Get Circle wallet balance.
        
        Args:
            db: Database session
            wallet_id: Our internal wallet ID
            
        Returns:
            CircleWalletBalance: Wallet balance
            
        Raises:
            NotFoundError: If wallet not found
        """
        wallet = await self.get_or_404(db, id=wallet_id)
        
        if wallet.type != SQLAlchemyWalletType.CIRCLE:
            raise NotFoundError(
                message=f"Wallet {wallet_id} is not a Circle wallet",
                entity="wallet"
            )
        
        config = wallet.metadata or {}
        circle_wallet_id = config.get('circle_wallet_id')
        circle_wallet_set_id = config.get('circle_wallet_set_id')
        
        if not circle_wallet_id or not circle_wallet_set_id:
            raise NotFoundError(
                message=f"Wallet {wallet_id} is missing Circle configuration",
                entity="wallet"
            )
        
        try:
            # Get balances from Circle - now returns dictionary
            balances_data = await circle_service.get_balances(
                wallet_id=circle_wallet_id
            )
            
            # Format the balances
            balances = []
            for balance in balances_data:
                balances.append({
                    "token": balance.get("token_id"),
                    "amount": balance.get("amount"),
                    "formatted_amount": str(Decimal(balance.get("amount", "0")) / Decimal(10**6)),  # Assuming 6 decimals (USDC)
                })
            
            return CircleWalletBalance(
                wallet_id=wallet_id,
                address=wallet.address,
                chain_id=wallet.chain_id,
                balances=balances,
                last_updated=datetime.utcnow()
            )
        except ExternalServiceError as e:
            logger.error(
                "get_circle_wallet_balance_failed",
                error=str(e),
                wallet_id=wallet_id
            )
            raise
            
    async def create_circle_wallet_transaction(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
        transaction_data: dict,
        organization_id: str,
    ) -> CircleWalletTransaction:
        """
        Create a transaction from a Circle wallet.

        Args:
            db: Database session
            wallet_id: Internal wallet ID
            transaction_data: Transaction details including destination address, amount, etc.
            organization_id: Organization ID for verification

        Returns:
            CircleWalletTransaction: Transaction details

        Raises:
            NotFoundError: If wallet not found
            ExternalServiceError: If Circle API call fails
        """
        try:
            # Get the internal wallet record to verify ownership and get Circle wallet ID
            wallet_query = select(Wallet).where(
                and_(
                    Wallet.id == wallet_id,
                    Wallet.organization_id == organization_id,
                    Wallet.type == WalletType.CIRCLE,
                    Wallet.is_active == True,
                )
            )
            wallet_result = await db.execute(wallet_query)
            wallet = wallet_result.scalar_one_or_none()

            if not wallet:
                raise NotFoundError(f"Wallet with ID {wallet_id} not found or not owned by organization")

            # Get Circle wallet ID from wallet metadata
            metadata = wallet.metadata or {}
            if not metadata.get("circle_wallet_id"):
                raise ValueError("Circle wallet ID not found in wallet metadata")

            circle_wallet_id = metadata["circle_wallet_id"]
            circle_wallet_set_id = metadata.get("circle_wallet_set_id")

            # Extract transaction parameters
            destination_address = transaction_data["destination_address"]
            amount = transaction_data["amount"]
            token_id = transaction_data.get("token_id", "USDC")
            fee_level = transaction_data.get("fee_level", "MEDIUM")
            idempotency_key = transaction_data.get("idempotency_key", str(uuid.uuid4()))

            # Create transaction in Circle
            response = await self.circle_service.create_transaction(
                wallet_id=circle_wallet_id,
                destination=destination_address,
                amount=amount,
                token_id=token_id,
                fee_level=fee_level,
                idempotency_key=idempotency_key,
            )

            # Map Circle transaction response to our schema
            transaction = CircleWalletTransaction(
                id=response["id"],
                wallet_id=wallet_id,
                destination_address=destination_address,
                amount=Decimal(amount),
                token_id=token_id,
                fee=Decimal(response.get("fee", "0")),
                source_address=response.get("source_address", ""),
                status=response["status"],
                transaction_hash=response.get("transaction_hash", None),
                created_at=datetime.fromisoformat(response["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(response["updated_at"].replace("Z", "+00:00")),
                block_number=response.get("block_number", None),
                block_hash=response.get("block_hash", None),
            )

            # Save transaction to blockchain_transactions table
            db_transaction = BlockchainTransaction(
                id=str(uuid.uuid4()),
                hash=response.get("transaction_hash", response["id"]),  # Use tx hash or Circle ID if hash not available yet
                chainId=wallet.chain_id,
                fromAddress=response.get("source_address", ""),
                toAddress=destination_address,
                value=str(amount),
                data=None,
                nonce=None,
                status=(BlockchainTxStatus.PENDING if response["status"] == "pending" 
                         else BlockchainTxStatus.MINED if response["status"] == "complete"
                         else BlockchainTxStatus.FAILED),
                error=None,
                walletId=wallet_id,
                gasPrice=None,
                gasLimit=None,
                gasUsed=response.get("fee", None),
                createdAt=datetime.now(),
                minedAt=None,
                metadata={
                    "circle_transaction_id": response["id"],
                    "token_id": token_id,
                    "circle_status": response["status"],
                    "raw_response": response,
                }
            )

            db.add(db_transaction)
            await db.commit()

            return transaction

        except SQLAlchemyError as e:
            await db.rollback()
            self.logger.error("Database error creating Circle wallet transaction", error=str(e))
            raise ExternalServiceError(f"Database error: {str(e)}")

        except (KeyError, ValueError) as e:
            self.logger.error("Invalid transaction data", error=str(e))
            raise ExternalServiceError(f"Invalid transaction data: {str(e)}")

        except Exception as e:
            self.logger.error("Error creating Circle wallet transaction", error=str(e))
            if hasattr(e, "__name__") and e.__class__.__name__ == "NotFoundError":
                raise
            raise ExternalServiceError(f"Failed to create transaction: {str(e)}")

    async def get_circle_wallet_transactions(
        self,
        db: AsyncSession,
        *,
        wallet_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page_size: int = 10,
        page_number: int = 1,
    ) -> List[CircleWalletTransaction]:
        """
        Get transactions for a Circle wallet.

        Args:
            db: Database session
            wallet_id: Internal wallet ID
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            page_size: Number of results per page
            page_number: Page number for pagination

        Returns:
            List[CircleWalletTransaction]: List of wallet transactions

        Raises:
            NotFoundError: If wallet not found
            ExternalServiceError: If Circle API call fails
        """
        try:
            # Get the internal wallet record
            wallet_query = select(Wallet).where(
                and_(
                    Wallet.id == wallet_id,
                    Wallet.type == WalletType.CIRCLE,
                    Wallet.is_active == True,
                )
            )
            wallet_result = await db.execute(wallet_query)
            wallet = wallet_result.scalar_one_or_none()

            if not wallet:
                raise NotFoundError(f"Wallet with ID {wallet_id} not found")

            # Get Circle wallet ID from wallet metadata
            metadata = wallet.metadata or {}
            if not metadata.get("circle_wallet_id"):
                raise ValueError("Circle wallet ID not found in wallet metadata")

            circle_wallet_id = metadata["circle_wallet_id"]

            # Get transactions from Circle - directly uses circle_service now
            transactions_data = await circle_service.get_wallet_transactions(
                wallet_id=circle_wallet_id,
                from_date=start_date,
                to_date=end_date,
                page_size=page_size,
                page_number=page_number,
            )

            # Map Circle transaction responses to our schema
            transactions = []
            for tx_data in transactions_data.get("data", []):
                # Handle possible missing or null fields in the dictionary response
                created_at_str = tx_data.get("created_at")
                updated_at_str = tx_data.get("updated_at")
                
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")) if created_at_str else datetime.utcnow()
                    updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00")) if updated_at_str else None
                except (ValueError, AttributeError):
                    created_at = datetime.utcnow()
                    updated_at = None
                    
                tx = CircleWalletTransaction(
                    id=tx_data.get("id", str(uuid.uuid4())),
                    wallet_id=wallet_id,
                    status=tx_data.get("status", "unknown"),
                    type=tx_data.get("type", "unknown"),
                    blockchain=tx_data.get("blockchain", ""),
                    from_address=tx_data.get("source_address", ""),
                    to_address=tx_data.get("destination_address", ""),
                    amount=tx_data.get("amount", ""),
                    token_id=tx_data.get("token_id", "USDC"),
                    created_at=created_at,
                    updated_at=updated_at,
                    hash=tx_data.get("transaction_hash"),
                    state=tx_data.get("state"),
                    error=tx_data.get("error")
                )
                transactions.append(tx)

            return transactions

        except ValueError as e:
            self.logger.error("Invalid wallet data", error=str(e))
            raise ExternalServiceError(f"Invalid wallet data: {str(e)}")

        except Exception as e:
            self.logger.error("Error getting Circle wallet transactions", error=str(e))
            if hasattr(e, "__class__") and e.__class__.__name__ == "NotFoundError":
                raise
            raise ExternalServiceError(f"Failed to get transactions: {str(e)}")

# Create singleton instance
circle_wallet_repository = CircleWalletRepository()
