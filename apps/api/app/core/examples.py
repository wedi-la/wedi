"""
OpenAPI Examples Module

This module provides example requests and responses for API documentation.
These examples are used throughout the application for consistent documentation.
"""
from datetime import datetime, timezone
from typing import Dict, Any


class AuthExamples:
    """Authentication endpoint examples."""
    
    login_request = {
        "standard": {
            "summary": "Standard login",
            "value": {
                "email": "john.doe@example.com",
                "password": "SecurePassword123!"
            }
        }
    }
    
    register_request = {
        "new_user": {
            "summary": "New user registration",
            "value": {
                "email": "jane.smith@example.com",
                "password": "MySecurePass456!",
                "full_name": "Jane Smith",
                "organization_name": "Acme Corp"
            }
        }
    }
    
    token_response = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": "usr_123456",
            "email": "john.doe@example.com",
            "full_name": "John Doe",
            "organization_id": "org_789012"
        }
    }


class OrganizationExamples:
    """Organization endpoint examples."""
    
    create_request = {
        "standard": {
            "summary": "Create organization",
            "value": {
                "name": "Tech Innovations Ltd",
                "display_name": "Tech Innovations",
                "country": "US",
                "tax_id": "12-3456789",
                "settings": {
                    "logo_url": "https://example.com/logo.png",
                    "primary_color": "#1a73e8"
                }
            }
        }
    }
    
    organization_response = {
        "id": "org_123456",
        "name": "Tech Innovations Ltd",
        "display_name": "Tech Innovations",
        "country": "US",
        "tax_id": "12-3456789",
        "settings": {
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#1a73e8"
        },
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }


class PaymentLinkExamples:
    """Payment link endpoint examples."""
    
    create_request = {
        "standard": {
            "summary": "Standard payment link",
            "description": "A typical payment link for an invoice",
            "value": {
                "amount": 1500.00,
                "currency": "USD",
                "description": "Invoice #2024-001 - Consulting Services",
                "reference_id": "INV-2024-001",
                "executing_agent_id": "550e8400-e29b-41d4-a716-446655440000",
                "expires_at": "2024-12-31T23:59:59Z",
                "metadata": {
                    "client_name": "Acme Corp",
                    "project": "Q1 Development",
                    "invoice_date": "2024-01-15"
                }
            }
        },
        "minimal": {
            "summary": "Minimal payment link",
            "description": "Payment link with only required fields",
            "value": {
                "amount": 100.00,
                "currency": "USD",
                "description": "Payment for services",
                "executing_agent_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        },
        "recurring": {
            "summary": "Recurring payment link",
            "description": "Payment link for subscription services",
            "value": {
                "amount": 99.99,
                "currency": "USD",
                "description": "Monthly subscription - Premium Plan",
                "reference_id": "SUB-2024-001",
                "executing_agent_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {
                    "subscription_type": "premium",
                    "billing_cycle": "monthly",
                    "customer_id": "cust_123456"
                }
            }
        }
    }
    
    payment_link_response = {
        "id": "pl_1234567890abcdef",
        "organization_id": "org_987654321",
        "amount": 1500.00,
        "currency": "USD",
        "description": "Invoice #2024-001 - Consulting Services",
        "reference_id": "INV-2024-001",
        "short_code": "PAY-ABC123",
        "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANS...",
        "status": "active",
        "executing_agent_id": "550e8400-e29b-41d4-a716-446655440000",
        "expires_at": "2024-12-31T23:59:59Z",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "created_by_id": "usr_123456",
        "metadata": {
            "client_name": "Acme Corp",
            "project": "Q1 Development",
            "invoice_date": "2024-01-15"
        }
    }
    
    update_request = {
        "update_description": {
            "summary": "Update description",
            "value": {
                "description": "Updated invoice description",
                "metadata": {
                    "notes": "Customer requested description change"
                }
            }
        },
        "cancel_link": {
            "summary": "Cancel payment link",
            "value": {
                "status": "cancelled",
                "metadata": {
                    "cancellation_reason": "Customer request"
                }
            }
        },
        "extend_expiry": {
            "summary": "Extend expiration date",
            "value": {
                "expires_at": "2025-06-30T23:59:59Z",
                "metadata": {
                    "extension_reason": "Customer requested more time"
                }
            }
        }
    }


class AgentExamples:
    """Agent endpoint examples."""
    
    create_request = {
        "payment_agent": {
            "summary": "Payment orchestration agent",
            "value": {
                "name": "Colombia Payment Agent",
                "type": "payment_orchestration",
                "status": "active",
                "capabilities": ["yoint_integration", "payment_routing"],
                "configuration": {
                    "primary_provider": "yoint",
                    "fallback_provider": "trubit",
                    "retry_attempts": 3
                }
            }
        }
    }
    
    agent_response = {
        "id": "agent_123456",
        "organization_id": "org_789012",
        "name": "Colombia Payment Agent",
        "type": "payment_orchestration",
        "status": "active",
        "capabilities": ["yoint_integration", "payment_routing"],
        "configuration": {
            "primary_provider": "yoint",
            "fallback_provider": "trubit",
            "retry_attempts": 3
        },
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }


class PaymentOrderExamples:
    """Payment order endpoint examples."""
    
    payment_order_response = {
        "id": "po_0987654321",
        "payment_link_id": "pl_1234567890",
        "organization_id": "org_987654321",
        "amount": 1500.00,
        "currency": "USD",
        "status": "processing",
        "provider": "yoint",
        "provider_reference": "YOINT-123456",
        "customer": {
            "email": "customer@example.com",
            "name": "John Customer",
            "phone": "+1234567890"
        },
        "created_at": "2024-01-15T11:00:00Z",
        "updated_at": "2024-01-15T11:01:00Z",
        "metadata": {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0..."
        }
    }


class WebhookExamples:
    """Webhook event examples."""
    
    payment_link_paid = {
        "event_type": "payment.link.paid",
        "event_id": "evt_550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2024-01-15T11:30:00Z",
        "data": {
            "payment_link_id": "pl_1234567890",
            "payment_order_id": "po_0987654321",
            "amount": 1500.00,
            "currency": "USD",
            "paid_at": "2024-01-15T11:29:45Z",
            "customer": {
                "email": "customer@example.com",
                "name": "John Customer"
            }
        }
    }
    
    payment_order_completed = {
        "event_type": "payment.order.completed",
        "event_id": "evt_660e8400-e29b-41d4-a716-446655440001",
        "timestamp": "2024-01-15T11:35:00Z",
        "data": {
            "payment_order_id": "po_0987654321",
            "status": "completed",
            "provider": "yoint",
            "provider_reference": "YOINT-123456",
            "completed_at": "2024-01-15T11:34:50Z",
            "settlement": {
                "amount": 1470.00,
                "currency": "USD",
                "fee": 30.00,
                "exchange_rate": 1.0
            }
        }
    }
    
    agent_action_performed = {
        "event_type": "agent.action.performed",
        "event_id": "evt_770e8400-e29b-41d4-a716-446655440002",
        "timestamp": "2024-01-15T11:32:00Z",
        "data": {
            "agent_id": "agent_123456",
            "action": "payment_provider_selected",
            "payment_order_id": "po_0987654321",
            "decision": {
                "provider": "yoint",
                "reasoning": "Best rates for Colombia to Mexico corridor",
                "confidence": 0.95
            }
        }
    }


class ErrorExamples:
    """Error response examples."""
    
    bad_request = {
        "detail": "Invalid request parameters",
        "errors": [
            {
                "field": "amount",
                "message": "Amount must be greater than 0"
            }
        ]
    }
    
    unauthorized = {
        "detail": "Invalid authentication credentials"
    }
    
    forbidden = {
        "detail": "You don't have permission to access this resource"
    }
    
    not_found = {
        "detail": "Resource not found"
    }
    
    conflict = {
        "detail": "Resource already exists",
        "conflict_id": "INV-2024-001"
    }
    
    validation_error = {
        "detail": [
            {
                "loc": ["body", "amount"],
                "msg": "ensure this value is greater than 0",
                "type": "value_error.number.not_gt",
                "ctx": {"limit_value": 0}
            }
        ]
    }


# Export all example classes
__all__ = [
    "AuthExamples",
    "OrganizationExamples", 
    "PaymentLinkExamples",
    "AgentExamples",
    "PaymentOrderExamples",
    "WebhookExamples",
    "ErrorExamples"
] 