"""
OpenAPI Configuration Module

This module provides configuration for API documentation including
metadata, tags, and Scalar documentation integration.
"""
from typing import Dict, List, Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced metadata and examples.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        OpenAPI schema dictionary
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Wedi Pay API",
        version="0.1.0",
        description="""
# Wedi Pay API Documentation

Welcome to the Wedi Pay API documentation. Wedi Pay is an AI-native, multi-tenant payment orchestration platform designed for B2B international payments.

## Overview

This API provides a comprehensive set of endpoints for managing payment operations, including:
- Payment link creation and management
- Multi-organization support
- Agent-based payment orchestration
- Real-time event streaming
- Webhook integrations

## Key Features

- **AI-Native**: Leverages autonomous agents for intelligent payment routing and optimization
- **Multi-Tenant**: Full support for B2B organizations with role-based access control
- **Event-Driven**: All operations emit events for real-time tracking and integration
- **International**: Focused on cross-border payments (MVP: Colombia to Mexico corridor)

## Authentication

All endpoints (except public payment link access) require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Rate Limiting

API requests are rate-limited to ensure fair usage:
- Standard tier: 100 requests per minute
- Premium tier: 1000 requests per minute

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages in the response body.

## Support

For API support, please contact: api-support@wedi.la
        """,
        routes=app.routes,
        tags=tags_metadata,
        servers=[
            {
                "url": "https://api.wedi.la",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.wedi.la", 
                "description": "Staging server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Local development server"
            }
        ],
        contact={
            "name": "Wedi Pay API Support",
            "email": "api-support@wedi.la",
            "url": "https://docs.wedi.la"
        },
        license_info={
            "name": "Proprietary",
            "url": "https://wedi.la/terms"
        },
    )
    
    # Add custom x-codeSamples for Scalar
    add_code_samples(openapi_schema)
    
    # Add webhook documentation
    add_webhook_documentation(openapi_schema)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Tags metadata for organizing endpoints
tags_metadata = [
    {
        "name": "Authentication",
        "description": "Operations related to user authentication and authorization",
        "externalDocs": {
            "description": "Authentication guide",
            "url": "https://docs.wedi.la/authentication"
        }
    },
    {
        "name": "Organizations", 
        "description": "Manage multi-tenant organizations and memberships"
    },
    {
        "name": "Users",
        "description": "User profile and management operations"
    },
    {
        "name": "Payment Links",
        "description": "Create and manage payment links for B2B transactions",
        "externalDocs": {
            "description": "Payment links guide",
            "url": "https://docs.wedi.la/payment-links"
        }
    },
    {
        "name": "Agents",
        "description": "AI agents that orchestrate payment operations"
    },
    {
        "name": "Payment Orders",
        "description": "Track and manage payment order execution"
    },
    {
        "name": "System",
        "description": "System status and health endpoints"
    },
    {
        "name": "Webhooks",
        "description": "Configure and manage webhook endpoints for real-time notifications"
    }
]


def add_code_samples(openapi_schema: Dict[str, Any]) -> None:
    """
    Add code samples for Scalar documentation.
    
    Args:
        openapi_schema: OpenAPI schema dictionary to modify
    """
    # Payment link creation example
    if "/api/v1/payment-links" in openapi_schema.get("paths", {}):
        create_endpoint = openapi_schema["paths"]["/api/v1/payment-links"].get("post", {})
        if create_endpoint:
            create_endpoint["x-codeSamples"] = [
                {
                    "lang": "Python",
                    "source": """import requests

headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}

data = {
    "amount": 100.00,
    "currency": "USD",
    "description": "Invoice #1234 - Consulting Services",
    "reference_id": "INV-2024-001",
    "executing_agent_id": "agent_123",
    "expires_at": "2024-12-31T23:59:59Z",
    "metadata": {
        "client_name": "Acme Corp",
        "invoice_date": "2024-01-15"
    }
}

response = requests.post(
    "https://api.wedi.la/api/v1/payment-links",
    json=data,
    headers=headers
)

print(response.json())"""
                },
                {
                    "lang": "JavaScript", 
                    "source": """const axios = require('axios');

const headers = {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
};

const data = {
    amount: 100.00,
    currency: 'USD',
    description: 'Invoice #1234 - Consulting Services',
    reference_id: 'INV-2024-001',
    executing_agent_id: 'agent_123',
    expires_at: '2024-12-31T23:59:59Z',
    metadata: {
        client_name: 'Acme Corp',
        invoice_date: '2024-01-15'
    }
};

axios.post('https://api.wedi.la/api/v1/payment-links', data, { headers })
    .then(response => console.log(response.data))
    .catch(error => console.error(error));"""
                },
                {
                    "lang": "cURL",
                    "source": """curl -X POST https://api.wedi.la/api/v1/payment-links \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "amount": 100.00,
    "currency": "USD",
    "description": "Invoice #1234 - Consulting Services",
    "reference_id": "INV-2024-001",
    "executing_agent_id": "agent_123",
    "expires_at": "2024-12-31T23:59:59Z",
    "metadata": {
        "client_name": "Acme Corp",
        "invoice_date": "2024-01-15"
    }
  }'"""
                }
            ]


def add_webhook_documentation(openapi_schema: Dict[str, Any]) -> None:
    """
    Add webhook documentation to OpenAPI schema.
    
    Args:
        openapi_schema: OpenAPI schema dictionary to modify
    """
    openapi_schema["webhooks"] = {
        "payment.link.paid": {
            "post": {
                "summary": "Payment Link Paid",
                "description": "Webhook triggered when a payment link is successfully paid",
                "requestBody": {
                    "description": "Payment link paid event payload",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "event_type": {
                                        "type": "string",
                                        "example": "payment.link.paid"
                                    },
                                    "event_id": {
                                        "type": "string",
                                        "format": "uuid",
                                        "example": "550e8400-e29b-41d4-a716-446655440000"
                                    },
                                    "timestamp": {
                                        "type": "string",
                                        "format": "date-time",
                                        "example": "2024-01-15T09:30:00Z"
                                    },
                                    "data": {
                                        "type": "object",
                                        "properties": {
                                            "payment_link_id": {
                                                "type": "string",
                                                "example": "pl_1234567890"
                                            },
                                            "amount": {
                                                "type": "number",
                                                "example": 100.00
                                            },
                                            "currency": {
                                                "type": "string",
                                                "example": "USD"
                                            },
                                            "payment_order_id": {
                                                "type": "string",
                                                "example": "po_0987654321"
                                            },
                                            "paid_at": {
                                                "type": "string",
                                                "format": "date-time",
                                                "example": "2024-01-15T09:29:45Z"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Webhook processed successfully"
                    }
                }
            }
        },
        "payment.order.completed": {
            "post": {
                "summary": "Payment Order Completed",
                "description": "Webhook triggered when a payment order is successfully completed",
                "requestBody": {
                    "description": "Payment order completed event payload",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "event_type": {
                                        "type": "string",
                                        "example": "payment.order.completed"
                                    },
                                    "event_id": {
                                        "type": "string",
                                        "format": "uuid"
                                    },
                                    "timestamp": {
                                        "type": "string",
                                        "format": "date-time"
                                    },
                                    "data": {
                                        "type": "object",
                                        "properties": {
                                            "payment_order_id": {
                                                "type": "string",
                                                "example": "po_0987654321"
                                            },
                                            "status": {
                                                "type": "string",
                                                "example": "completed"
                                            },
                                            "provider": {
                                                "type": "string",
                                                "example": "yoint"
                                            },
                                            "completed_at": {
                                                "type": "string",
                                                "format": "date-time"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Webhook processed successfully"
                    }
                }
            }
        }
    }


def configure_scalar_ui(app: FastAPI) -> None:
    """
    Configure Scalar UI for API documentation.
    
    Args:
        app: FastAPI application instance
    """
    from fastapi.responses import HTMLResponse
    
    @app.get("/docs", include_in_schema=False)
    async def scalar_docs() -> HTMLResponse:
        """Serve Scalar documentation UI."""
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>Wedi Pay API - Documentation</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <script id="api-reference" data-url="/openapi.json"></script>
    <script>
        var configuration = {{
            theme: 'purple',
            layout: 'modern',
            searchHotKey: 'k',
            darkMode: true,
            hiddenClients: [],
            authentication: {{
                preferredSecurityScheme: 'bearerAuth',
                apiKey: {{
                    token: 'YOUR_JWT_TOKEN'
                }}
            }}
        }};
        
        document.getElementById('api-reference').dataset.configuration = JSON.stringify(configuration);
    </script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
</body>
</html>
        """, media_type="text/html") 