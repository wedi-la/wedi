"""API version 1 routers.

This module contains all the routers for API v1 endpoints.
"""
from fastapi import APIRouter

from app.routers import auth, circle_wallet, organizations, payment_links, users

# Create the main v1 router
router = APIRouter(
    prefix="/api/v1",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
    },
)

# Include all routers
router.include_router(auth.router)
router.include_router(circle_wallet.router)
router.include_router(organizations.router)
router.include_router(users.router)
router.include_router(payment_links.router)

# Future routers to be added:
# router.include_router(agents.router)
# router.include_router(payment_orders.router)
# router.include_router(customers.router)
# router.include_router(products.router)
# router.include_router(webhooks.router) 