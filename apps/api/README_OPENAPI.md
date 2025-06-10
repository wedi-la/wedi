# Wedi Pay API - OpenAPI Documentation

This document describes the OpenAPI documentation configuration for the Wedi Pay API.

## Overview

The Wedi Pay API uses **Scalar** for interactive API documentation, providing a modern and user-friendly interface for exploring and testing API endpoints.

## Accessing Documentation

### Development Environment

When running the API in development mode, you can access the documentation at:

- **Scalar UI**: `http://localhost:8000/docs`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`
- **ReDoc**: `http://localhost:8000/redoc` (alternative documentation)

### Production Environment

API documentation is disabled in production for security reasons. The documentation URLs will return 404 responses.

## Documentation Features

### 1. **Interactive API Explorer**
- Test endpoints directly from the documentation
- Automatic request/response examples
- Built-in authentication support

### 2. **Code Samples**
Each endpoint includes code samples in multiple languages:
- Python (using requests)
- JavaScript (using axios)
- cURL commands

### 3. **Webhook Documentation**
The API documentation includes webhook event schemas for:
- `payment.link.paid` - Triggered when a payment link is paid
- `payment.order.completed` - When a payment order is completed
- `agent.action.performed` - When an AI agent performs an action

### 4. **Request/Response Examples**
All endpoints include realistic examples:
- Multiple request variations (standard, minimal, edge cases)
- Complete response structures
- Error response formats

## API Organization

The API is organized into the following tags:

- **Authentication**: User authentication and JWT token management
- **Organizations**: Multi-tenant organization management
- **Users**: User profile and account management
- **Payment Links**: Payment link creation and management
- **Agents**: AI agent configuration (coming soon)
- **Payment Orders**: Payment order tracking (coming soon)
- **System**: Health checks and status endpoints
- **Webhooks**: Webhook configuration (coming soon)

## Authentication

All endpoints (except public payment link access) require JWT authentication:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" https://api.wedi.pay/api/v1/...
```

## Rate Limiting

- **Standard tier**: 100 requests per minute
- **Premium tier**: 1000 requests per minute

## Example Usage

### Creating a Payment Link

```python
import requests

headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}

data = {
    "amount": 100.00,
    "currency": "USD",
    "description": "Invoice #1234",
    "executing_agent_id": "agent_123",
    "expires_at": "2024-12-31T23:59:59Z"
}

response = requests.post(
    "https://api.wedi.pay/api/v1/payment-links",
    json=data,
    headers=headers
)

print(response.json())
```

## Extending Documentation

### Adding Examples

Examples are centralized in `app/core/examples.py`. To add new examples:

```python
class YourExamples:
    """Your endpoint examples."""
    
    create_request = {
        "standard": {
            "summary": "Standard request",
            "value": {
                "field": "value"
            }
        }
    }
```

### Adding Code Samples

Code samples are added in the `add_code_samples()` function in `app/core/openapi.py`:

```python
create_endpoint["x-codeSamples"] = [
    {
        "lang": "Python",
        "source": "your code here"
    }
]
```

### Custom Scalar Configuration

The Scalar UI is configured in `configure_scalar_ui()` with:
- Dark mode enabled by default
- Purple theme
- Search hotkey: 'k'
- Bearer auth pre-configured

## Development Tips

1. **Auto-reload**: The documentation updates automatically when you modify endpoint definitions
2. **Validation**: FastAPI validates all examples against the Pydantic models
3. **Testing**: Use the "Try it out" feature in Scalar to test endpoints directly
4. **Export**: You can export the OpenAPI spec as JSON for use with other tools

## API Design Principles

1. **RESTful**: Follow REST principles for resource design
2. **Consistent**: Use consistent naming and response formats
3. **Descriptive**: Include detailed descriptions for all endpoints
4. **Examples**: Provide realistic, working examples
5. **Errors**: Document all possible error responses

## Support

For API support or documentation issues:
- Email: api-support@wedi.pay
- Documentation: https://docs.wedi.pay 