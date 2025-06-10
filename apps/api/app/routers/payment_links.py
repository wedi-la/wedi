"""
Payment links router for creating and managing payment links.

This module provides endpoints for:
- Creating payment links with agent validation
- Listing and searching payment links
- Updating payment link status
- Public access to payment links via short code
- Archiving and duplicating payment links
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
import nanoid

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.examples import PaymentLinkExamples, ErrorExamples
from app.db.unit_of_work import UnitOfWork, get_unit_of_work
from app.events.domain_events import (
    PaymentLinkCreatedEvent,
    PaymentLinkUpdatedEvent,
    PaymentLinkArchivedEvent
)
from app.events.event_publisher import get_event_publisher, EventPublisher
from app.models import PaymentLinkStatus, User
from app.repositories.agent import AgentRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.payment_link import PaymentLinkRepository
from app.schemas.payment_link import (
    PaymentLinkCreate,
    PaymentLinkUpdate,
    PaymentLink,
    PaymentLinkWithStats,
    PaymentLinkListResponse,
    PaymentLinkPublicResponse,
    PaymentLinkSearchParams,
    PaymentLinkSearchResponse
)
router = APIRouter(
    prefix="/payment-links",
    tags=["Payment Links"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Payment link not found"},
    },
)


def generate_short_code() -> str:
    """Generate a unique short code for payment links."""
    # Generate a 10-character alphanumeric code
    return f"PAY-{nanoid.generate(size=7)}"


def generate_qr_code(payment_url: str) -> str:
    """Generate QR code for payment link (placeholder)."""
    # TODO: Implement actual QR code generation
    return f"qr_code_for_{payment_url}"


@router.get(
    "/",
    response_model=PaymentLinkListResponse,
    summary="List payment links",
    description="List all payment links for the authenticated organization",
    response_description="Paginated list of payment links",
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "items": [PaymentLinkExamples.payment_link_response],
                        "total": 1,
                        "page": 1,
                        "limit": 20,
                        "has_next": False
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": ErrorExamples.unauthorized
                }
            }
        }
    }
)
async def list_payment_links(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
    status: Optional[PaymentLinkStatus] = Query(
        None,
        description="Filter by payment link status"
    ),
    currency: Optional[str] = Query(
        None,
        description="Filter by currency code (e.g., USD, COP)"
    ),
    created_by_id: Optional[str] = Query(
        None,
        description="Filter by creator user ID"
    ),
    smart_contract_address: Optional[str] = Query(
        None,
        description="Filter by smart contract address"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaymentLinkListResponse:
    """
    List payment links with optional filtering.
    
    Requires authentication and returns only links for the user's organization.
    """
    async with uow:
        # Build filters
        filters = {"organization_id": current_user.organization_id}
        if status:
            filters["status"] = status
        if currency:
            filters["currency"] = currency.upper()
        if created_by_id:
            filters["created_by_id"] = created_by_id
        if smart_contract_address:
            filters["smart_contract_address"] = smart_contract_address
        
        # Get payment links
        payment_links = await uow.payment_links.get_multi(
            db=uow.session,
            skip=(page - 1) * limit,
            limit=limit,
            organization_id=current_user.organization_id,
            filters=filters
        )
        
        # Get total count
        total = await uow.payment_links.count(
            db=uow.session,
            organization_id=current_user.organization_id,
            filters=filters
        )
        
        # Convert to response format
        items = []
        for link in payment_links:
            item = {
                "id": str(link.id),
                "title": link.title,
                "amount": link.amount,
                "currency": link.currency,
                "status": link.status,
                "short_code": link.short_code,
                "payment_url": f"https://pay.wedi.co/{link.short_code}",
                "created_at": link.created_at,
                "expires_at": link.expires_at,
                "total_payments": 0  # TODO: Calculate from payment orders
            }
            items.append(item)
        
        return PaymentLinkListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_next=(page * limit) < total
        )


@router.post(
    "/",
    response_model=PaymentLink,
    status_code=status.HTTP_201_CREATED,
    summary="Create payment link",
    description="Create a new payment link with optional agent assignment",
    response_description="Created payment link details",
    responses={
        201: {
            "description": "Payment link created successfully",
            "content": {
                "application/json": {
                    "example": PaymentLinkExamples.payment_link_response
                }
            }
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": ErrorExamples.bad_request
                }
            }
        },
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Agent 550e8400-e29b-41d4-a716-446655440000 not found"}
                }
            }
        },
        409: {
            "description": "Conflict - duplicate reference_id",
            "content": {
                "application/json": {
                    "example": {"detail": "Payment link with reference_id 'INV-2024-001' already exists"}
                }
            }
        }
    }
)
async def create_payment_link(
    payment_link: PaymentLinkCreate = Body(
        ...,
        examples=PaymentLinkExamples.create_request
    ),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
    event_publisher: EventPublisher = Depends(get_event_publisher)
) -> PaymentLink:
    """
    Create a new payment link.
    
    If an executing_agent_id is provided, validates that the agent exists
    and is active before assignment.
    """
    async with uow:
        # Validate agent if provided
        if payment_link.executing_agent_id:
            agent = await uow.agents.get(
                db=uow.session,
                id=payment_link.executing_agent_id
            )
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent {payment_link.executing_agent_id} not found"
                )
            if not agent.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Agent {payment_link.executing_agent_id} is not active"
                )
        
        # Check for duplicate reference_id within organization
        if payment_link.reference_id:
            existing = await uow.payment_links.get_by_reference_id(
                db=uow.session,
                organization_id=current_user.organization_id,
                reference_id=payment_link.reference_id
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Payment link with reference_id '{payment_link.reference_id}' already exists"
                )
        
        # Generate short code and QR code
        short_code = generate_short_code()
        payment_url = f"https://pay.wedi.co/{short_code}"
        qr_code = generate_qr_code(payment_url)
        
        # Create payment link
        db_payment_link = await uow.payment_links.create(
            db=uow.session,
            obj_in={
                **payment_link.model_dump(exclude_unset=True, exclude={'metadata', 'theme'}),
                "organization_id": current_user.organization_id,
                "created_by_id": current_user.id,
                "short_code": short_code,
                "qr_code": qr_code,
                "status": PaymentLinkStatus.ACTIVE
            }
        )
        
        await uow.commit()
        
        # Emit event
        await event_publisher.publish(
            PaymentLinkCreatedEvent(
                payment_link_id=str(db_payment_link.id),
                organization_id=current_user.organization_id,
                amount=payment_link.amount,
                currency=payment_link.currency,
                short_code=short_code
            )
        )
        
        # Convert to response schema
        return PaymentLink.model_validate(db_payment_link)


@router.get(
    "/active",
    response_model=PaymentLinkListResponse,
    summary="List active payment links",
    description="List only active payment links",
    response_description="List of active payment links"
)
async def list_active_payment_links(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> PaymentLinkListResponse:
    """Get only active payment links for quick access."""
    return await list_payment_links(
        current_user=current_user,
        uow=uow,
        status=PaymentLinkStatus.ACTIVE,
        page=page,
        limit=limit
    )


@router.get(
    "/search",
    response_model=PaymentLinkSearchResponse,
    summary="Search payment links",
    description="Advanced search with multiple filters",
    response_description="Search results with applied filters"
)
async def search_payment_links(
    search_params: PaymentLinkSearchParams = Depends(),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> PaymentLinkSearchResponse:
    """
    Advanced search for payment links.
    
    Supports:
    - Text search in title, description, reference_id
    - Date range filters
    - Amount range filters
    - Multiple status filters
    """
    async with uow:
        # Build search filters
        filters = {"organization_id": current_user.organization_id}
        filters_applied = {}
        
        if search_params.status:
            filters["status"] = search_params.status
            filters_applied["status"] = search_params.status
            
        if search_params.currency:
            filters["currency"] = search_params.currency.upper()
            filters_applied["currency"] = search_params.currency.upper()
            
        if search_params.created_by_id:
            filters["created_by_id"] = search_params.created_by_id
            filters_applied["created_by_id"] = search_params.created_by_id
            
        if search_params.smart_contract_address:
            filters["smart_contract_address"] = search_params.smart_contract_address
            filters_applied["smart_contract_address"] = search_params.smart_contract_address
        
        # TODO: Implement text search and range filters in repository
        # For now, use basic filtering
        
        payment_links = await uow.payment_links.get_multi(
            db=uow.session,
            skip=(search_params.page - 1) * search_params.limit,
            limit=search_params.limit,
            organization_id=current_user.organization_id,
            filters=filters
        )
        
        total = await uow.payment_links.count(
            db=uow.session,
            organization_id=current_user.organization_id,
            filters=filters
        )
        
        # Convert to response format
        items = [PaymentLink.model_validate(link) for link in payment_links]
        
        return PaymentLinkSearchResponse(
            items=items,
            total=total,
            page=search_params.page,
            limit=search_params.limit,
            query=search_params.query,
            filters_applied=filters_applied
        )


@router.get(
    "/{payment_link_id}",
    response_model=PaymentLinkWithStats,
    summary="Get payment link details",
    description="Get detailed information about a specific payment link",
    response_description="Payment link with statistics",
    responses={
        200: {
            "description": "Payment link details with statistics",
            "content": {
                "application/json": {
                    "example": {
                        **PaymentLinkExamples.payment_link_response,
                        "total_payments": 5,
                        "total_amount_collected": 7500.00,
                        "success_rate": 0.8,
                        "average_payment_time": "PT1H30M"
                    }
                }
            }
        },
        404: {
            "description": "Payment link not found",
            "content": {
                "application/json": {
                    "example": ErrorExamples.not_found
                }
            }
        }
    }
)
async def get_payment_link(
    payment_link_id: UUID = Path(..., description="Payment link ID"),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> PaymentLinkWithStats:
    """
    Get payment link details including payment statistics.
    
    Returns:
    - Full payment link details
    - Payment statistics (total collected, success rate, etc.)
    """
    async with uow:
        payment_link = await uow.payment_links.get(
            db=uow.session,
            id=str(payment_link_id),
            organization_id=current_user.organization_id
        )
        
        if not payment_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment link not found"
            )
        
        # TODO: Calculate statistics from payment orders
        stats = {
            "total_payments": 0,
            "total_amount_collected": 0,
            "success_rate": 0.0,
            "average_payment_time": None
        }
        
        # Convert to response schema with stats
        response = PaymentLinkWithStats.model_validate(payment_link)
        for key, value in stats.items():
            setattr(response, key, value)
            
        return response


@router.get(
    "/by-short-code/{short_code}",
    response_model=PaymentLinkPublicResponse,
    summary="Get payment link by short code",
    description="Public endpoint to get payment link information",
    response_description="Public payment link information",
    responses={
        200: {
            "description": "Public payment link information",
            "content": {
                "application/json": {
                    "example": {
                        "id": "pl_1234567890abcdef",
                        "title": "Invoice #2024-001",
                        "description": "Invoice #2024-001 - Consulting Services",
                        "amount": 1500.00,
                        "currency": "USD",
                        "target_amount": 1500.00,
                        "target_currency": "MXN",
                        "status": "active",
                        "requires_kyc": False,
                        "expires_at": "2024-12-31T23:59:59Z",
                        "theme": {
                            "primary_color": "#1a73e8",
                            "logo_url": "https://example.com/logo.png"
                        },
                        "redirect_urls": {
                            "success": "https://example.com/success",
                            "failure": "https://example.com/failure"
                        },
                        "organization_name": "Tech Innovations Ltd"
                    }
                }
            }
        },
        404: {
            "description": "Payment link not found",
            "content": {
                "application/json": {
                    "example": ErrorExamples.not_found
                }
            }
        }
    }
)
async def get_payment_link_by_short_code(
    short_code: str = Path(
        ...,
        description="Payment link short code",
        example="PAY-ABC123"
    ),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> PaymentLinkPublicResponse:
    """
    Get payment link information by short code.
    
    This is a public endpoint used by the payment page.
    Returns only non-sensitive information.
    """
    async with uow:
        payment_link = await uow.payment_links.get_by_short_code(
            db=uow.session,
            short_code=short_code
        )
        
        if not payment_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment link not found"
            )
        
        # Check if expired
        if payment_link.expires_at and payment_link.expires_at < datetime.now(timezone.utc):
            if payment_link.status == PaymentLinkStatus.ACTIVE:
                # Auto-expire the link
                payment_link.status = PaymentLinkStatus.EXPIRED
                await uow.commit()
        
        # Get organization name
        organization = await uow.organizations.get(
            db=uow.session,
            id=payment_link.organization_id
        )
        
        # Return public information
        return PaymentLinkPublicResponse(
            id=str(payment_link.id),
            title=payment_link.title,
            description=payment_link.description,
            amount=payment_link.amount,
            currency=payment_link.currency,
            target_amount=payment_link.target_amount,
            target_currency=payment_link.target_currency,
            status=payment_link.status,
            requires_kyc=payment_link.requires_kyc,
            expires_at=payment_link.expires_at,
            theme=None,  # Not available in generated model
            redirect_urls=payment_link.redirect_urls,
            organization_name=organization.name if organization else None
        )


@router.patch(
    "/{payment_link_id}",
    response_model=PaymentLink,
    summary="Update payment link",
    description="Update payment link details or status",
    response_description="Updated payment link",
    responses={
        200: {
            "description": "Payment link updated successfully",
            "content": {
                "application/json": {
                    "example": PaymentLinkExamples.payment_link_response
                }
            }
        },
        400: {
            "description": "Invalid status transition",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot transition from EXPIRED to ACTIVE"}
                }
            }
        },
        404: {
            "description": "Payment link not found",
            "content": {
                "application/json": {
                    "example": ErrorExamples.not_found
                }
            }
        }
    }
)
async def update_payment_link(
    payment_link_id: UUID = Path(..., description="Payment link ID"),
    payment_link_update: PaymentLinkUpdate = Body(
        ...,
        examples=PaymentLinkExamples.update_request
    ),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
    event_publisher: EventPublisher = Depends(get_event_publisher)
) -> PaymentLink:
    """
    Update payment link details.
    
    Status transitions:
    - ACTIVE -> PAUSED, EXPIRED, COMPLETED
    - PAUSED -> ACTIVE, EXPIRED
    - Cannot update EXPIRED or COMPLETED links
    """
    async with uow:
        payment_link = await uow.payment_links.get(
            db=uow.session,
            id=str(payment_link_id),
            organization_id=current_user.organization_id
        )
        
        if not payment_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment link not found"
            )
        
        # Validate status transitions
        if payment_link_update.status:
            current_status = payment_link.status
            new_status = payment_link_update.status
            
            # Define valid transitions
            valid_transitions = {
                PaymentLinkStatus.ACTIVE: [
                    PaymentLinkStatus.PAUSED,
                    PaymentLinkStatus.EXPIRED,
                    PaymentLinkStatus.COMPLETED
                ],
                PaymentLinkStatus.PAUSED: [
                    PaymentLinkStatus.ACTIVE,
                    PaymentLinkStatus.EXPIRED
                ],
                PaymentLinkStatus.EXPIRED: [],
                PaymentLinkStatus.COMPLETED: []
            }
            
            if new_status not in valid_transitions.get(current_status, []):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot transition from {current_status} to {new_status}"
                )
        
        # Update payment link
        old_status = payment_link.status if payment_link_update.status else None
        updated_payment_link = await uow.payment_links.update(
            db=uow.session,
            db_obj=payment_link,
            obj_in=payment_link_update.model_dump(exclude_unset=True)
        )
        
        await uow.commit()
        
        # Emit event
        await event_publisher.publish(
            PaymentLinkUpdatedEvent(
                payment_link_id=str(updated_payment_link.id),
                organization_id=current_user.organization_id,
                updated_by=current_user.id,
                old_status=old_status.value if old_status and payment_link_update.status else None,
                new_status=updated_payment_link.status.value if payment_link_update.status else None
            )
        )
        
        return PaymentLink.model_validate(updated_payment_link)


@router.post(
    "/{payment_link_id}/archive",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive payment link",
    description="Soft delete a payment link",
    responses={
        204: {
            "description": "Payment link archived successfully"
        },
        400: {
            "description": "Payment link already archived",
            "content": {
                "application/json": {
                    "example": {"detail": "Payment link is already archived"}
                }
            }
        },
        404: {
            "description": "Payment link not found",
            "content": {
                "application/json": {
                    "example": ErrorExamples.not_found
                }
            }
        }
    }
)
async def archive_payment_link(
    payment_link_id: UUID = Path(..., description="Payment link ID to archive"),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
    event_publisher: EventPublisher = Depends(get_event_publisher)
) -> None:
    """
    Archive (soft delete) a payment link.
    
    Archived links:
    - Cannot receive new payments
    - Are hidden from default listings
    - Can be restored if needed
    """
    async with uow:
        payment_link = await uow.payment_links.get(
            db=uow.session,
            id=str(payment_link_id),
            organization_id=current_user.organization_id
        )
        
        if not payment_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment link not found"
            )
        
        # Check if already archived
        if payment_link.status == PaymentLinkStatus.EXPIRED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment link is already archived"
            )
        
        # TODO: Check for pending payments before archiving
        
        # Archive the payment link
        payment_link.status = PaymentLinkStatus.EXPIRED
        await uow.commit()
        
        # Emit event
        await event_publisher.publish(
            PaymentLinkArchivedEvent(
                payment_link_id=str(payment_link.id),
                organization_id=current_user.organization_id,
                archived_by=current_user.id
            )
        )


@router.post(
    "/{payment_link_id}/duplicate",
    response_model=PaymentLink,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate payment link",
    description="Create a copy of an existing payment link",
    response_description="New payment link created from duplicate",
    responses={
        201: {
            "description": "Payment link duplicated successfully",
            "content": {
                "application/json": {
                    "example": {
                        **PaymentLinkExamples.payment_link_response,
                        "title": "Invoice #2024-001 - Consulting Services (Copy)",
                        "reference_id": None
                    }
                }
            }
        },
        404: {
            "description": "Original payment link not found",
            "content": {
                "application/json": {
                    "example": ErrorExamples.not_found
                }
            }
        }
    }
)
async def duplicate_payment_link(
    payment_link_id: UUID = Path(..., description="Payment link ID to duplicate"),
    updates: Optional[PaymentLinkCreate] = Body(
        None,
        description="Optional modifications to apply to the duplicate",
        examples={
            "modify_amount": {
                "summary": "Duplicate with different amount",
                "value": {
                    "amount": 2000.00,
                    "description": "Updated invoice amount"
                }
            },
            "new_reference": {
                "summary": "Duplicate with new reference",
                "value": {
                    "reference_id": "INV-2024-002",
                    "title": "Invoice #2024-002"
                }
            }
        }
    ),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
    event_publisher: EventPublisher = Depends(get_event_publisher)
) -> PaymentLink:
    """
    Duplicate an existing payment link.
    
    Creates a new payment link with:
    - Same configuration as the original
    - New short code and QR code
    - Optional modifications via the updates parameter
    - Status set to ACTIVE
    """
    async with uow:
        original = await uow.payment_links.get(
            db=uow.session,
            id=str(payment_link_id),
            organization_id=current_user.organization_id
        )
        
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment link not found"
            )
        
        # Create duplicate data
        duplicate_data = PaymentLinkCreate(
            title=f"{original.title} (Copy)",
            description=original.description,
            reference_id=None,  # Clear reference ID to avoid conflicts
            amount=original.amount,
            currency=original.currency,
            target_amount=original.target_amount,
            target_currency=original.target_currency,
            allow_multiple_payments=original.allow_multiple_payments,
            requires_kyc=original.requires_kyc,
            expires_at=original.expires_at,
            redirect_urls=original.redirect_urls,
            # metadata and theme not available in generated model
            smart_contract_address=original.smart_contract_address,
            smart_contract_chain_id=original.smart_contract_chain_id,
            token_address=original.token_address,
            executing_agent_id=original.executing_agent_id
        )
        
        # Apply any updates
        if updates:
            update_data = updates.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(duplicate_data, field, value)
        
        # Create the duplicate
        return await create_payment_link(
            payment_link=duplicate_data,
            current_user=current_user,
            uow=uow,
            event_publisher=event_publisher
        ) 