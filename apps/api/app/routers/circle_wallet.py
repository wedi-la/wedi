"""
API routes for Circle wallet operations.
"""
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_organization_id,
    get_current_user_id,
    get_db,
    require_active_organization,
)
from app.core.exceptions import ExternalServiceError, NotFoundError
from app.repositories.wallet_circle import circle_wallet_repository
from app.schemas.wallet import (
    CircleWallet,
    CircleWalletBalance,
    CircleWalletCreate,
    CircleWalletSet,
    CircleWalletSetCreate,
    CircleWalletTransaction,
)

router = APIRouter(prefix="/circle-wallets", tags=["Wallets"])


@router.post("/sets", response_model=CircleWalletSet, status_code=status.HTTP_201_CREATED)
async def create_wallet_set(
    wallet_set: CircleWalletSetCreate,
    db: AsyncSession = Depends(get_db),
    organization_id: str = Depends(require_active_organization),
):
    """
    Create a new Circle wallet set.
    
    This endpoint creates a new wallet set in Circle and associates it with the organization.
    """
    try:
        result = await circle_wallet_repository.create_wallet_set(
            db=db,
            wallet_set=wallet_set,
            organization_id=organization_id,
        )
        return result
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create wallet set: {str(e)}"
        )


@router.post("/", response_model=CircleWallet, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    wallet: CircleWalletCreate,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id),
    organization_id: Optional[str] = Depends(get_current_organization_id),
):
    """
    Create a new Circle wallet.
    
    This endpoint creates a new wallet in a specified Circle wallet set.
    Either user_id or organization_id must be provided.
    """
    if not user_id and not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either user or organization must be authenticated"
        )
        
    try:
        result = await circle_wallet_repository.create_circle_wallet(
            db=db,
            wallet_data=wallet,
            user_id=user_id,
            organization_id=organization_id,
        )
        return result
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create wallet: {str(e)}"
        )


@router.get("/sets/{wallet_set_id}/wallets", response_model=List[CircleWallet])
async def get_wallets_by_set(
    wallet_set_id: str = Path(..., title="Wallet Set ID"),
    db: AsyncSession = Depends(get_db),
    organization_id: str = Depends(require_active_organization),
):
    """
    Get all wallets in a Circle wallet set.
    
    This endpoint retrieves all wallets associated with a specific wallet set.
    """
    try:
        wallets = await circle_wallet_repository.get_circle_wallets_by_set(
            db=db,
            wallet_set_id=wallet_set_id,
        )
        return wallets
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to get wallets: {str(e)}"
        )


@router.get("/{wallet_id}", response_model=CircleWallet)
async def get_wallet(
    wallet_id: str = Path(..., title="Wallet ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Circle wallet by ID.
    
    This endpoint retrieves a specific Circle wallet by our internal wallet ID.
    """
    try:
        wallet = await circle_wallet_repository.get_circle_wallet(
            db=db,
            wallet_id=wallet_id,
        )
        return wallet
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to get wallet: {str(e)}"
        )


@router.get("/{wallet_id}/balance", response_model=CircleWalletBalance)
async def get_wallet_balance(
    wallet_id: str = Path(..., title="Wallet ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Circle wallet balance.
    
    This endpoint retrieves the balance of a specific Circle wallet.
    """
    try:
        balance = await circle_wallet_repository.get_circle_wallet_balance(
            db=db,
            wallet_id=wallet_id,
        )
        return balance
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to get wallet balance: {str(e)}"
        )


@router.post("/{wallet_id}/transactions", response_model=CircleWalletTransaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    wallet_id: str = Path(..., title="Wallet ID"),
    transaction_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    organization_id: str = Depends(require_active_organization),
):
    """
    Create a new transaction from a Circle wallet.
    
    This endpoint initiates a transaction from the specified Circle wallet.
    """
    try:
        transaction = await circle_wallet_repository.create_circle_wallet_transaction(
            db=db,
            wallet_id=wallet_id,
            transaction_data=transaction_data,
            organization_id=organization_id,
        )
        return transaction
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create transaction: {str(e)}"
        )


@router.get("/{wallet_id}/transactions", response_model=List[CircleWalletTransaction])
async def get_wallet_transactions(
    wallet_id: str = Path(..., title="Wallet ID"),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    page_number: int = Query(1, ge=1, description="Page number"),
):
    """
    Get Circle wallet transactions.
    
    This endpoint retrieves the transaction history of a specific Circle wallet.
    """
    try:
        transactions = await circle_wallet_repository.get_circle_wallet_transactions(
            db=db,
            wallet_id=wallet_id,
            start_date=start_date,
            end_date=end_date,
            page_size=page_size,
            page_number=page_number,
        )
        return transactions
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to get wallet transactions: {str(e)}"
        )
