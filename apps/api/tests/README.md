# FastAPI Tests

This directory contains the test suite for the Wedi Pay FastAPI backend.

## Structure

```
tests/
├── api/v1/          # API endpoint tests
│   ├── test_auth.py
│   ├── test_organizations.py
│   ├── test_users.py
│   └── test_payment_links.py
├── factories/       # Test data factories
│   ├── user_factory.py
│   ├── organization_factory.py
│   └── payment_factory.py
├── fixtures/        # Additional test fixtures
├── utils/           # Test utilities
│   └── auth.py      # Authentication helpers
└── conftest.py      # Global pytest configuration
```

## Running Tests

### Run all tests:
```bash
poetry run pytest
```

### Run with coverage:
```bash
poetry run pytest --cov=app --cov-report=html
```

### Run specific test file:
```bash
poetry run pytest tests/api/v1/test_auth.py
```

### Run specific test class or function:
```bash
poetry run pytest tests/api/v1/test_auth.py::TestAuthEndpoints::test_login_creates_new_user
```

### Run tests by marker:
```bash
# Run only unit tests
poetry run pytest -m unit

# Run only integration tests
poetry run pytest -m integration

# Skip slow tests
poetry run pytest -m "not slow"
```

## Writing Tests

### 1. Use Async Tests
All endpoint tests should be async:
```python
@pytest.mark.asyncio
async def test_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/endpoint")
    assert response.status_code == 200
```

### 2. Use Factories for Test Data
```python
from tests.factories.user_factory import UserFactory

user = await UserFactory.create_user(db_session)
```

### 3. Test Authentication
```python
from tests.utils.auth import get_auth_headers

headers = get_auth_headers(user)
response = await client.get("/protected", headers=headers)
```

### 4. Test Organization Context
```python
headers = get_auth_headers(user)
headers["X-Organization-ID"] = org.id
response = await client.get("/org-endpoint", headers=headers)
```

## Test Categories

### Authentication Tests (`test_auth.py`)
- SIWE payload generation
- User login/registration
- Token refresh
- JWT validation

### Organization Tests (`test_organizations.py`)
- CRUD operations
- Member management
- Role-based access control
- Statistics

### User Tests (`test_users.py`)
- Profile management
- Wallet management
- Admin operations
- User deletion

### Payment Link Tests (`test_payment_links.py`)
- Link creation and management
- Public access endpoints
- Search and filtering
- Permissions

## Common Patterns

### Error Testing
```python
# Test 404
response = await client.get(f"/api/v1/resource/{non_existent_id}")
assert response.status_code == 404

# Test 403 Forbidden
response = await client.put(f"/api/v1/resource/{id}", headers=unauthorized_headers)
assert response.status_code == 403

# Test 409 Conflict
response = await client.post("/api/v1/resource", json=duplicate_data)
assert response.status_code == 409
```

### Pagination Testing
```python
response = await client.get("/api/v1/resources?skip=10&limit=5")
assert len(response.json()) <= 5
```

### Search Testing
```python
response = await client.get("/api/v1/resources/search?query=test")
data = response.json()
assert all("test" in item["name"].lower() for item in data)
```

## Coverage Requirements

The project is configured to require 80% test coverage. Coverage reports are generated in:
- Terminal output
- `htmlcov/` directory (HTML report)
- `coverage.xml` (XML report for CI/CD)

## Continuous Integration

Tests are automatically run in CI/CD pipeline on:
- Pull requests
- Pushes to main branch
- Release tags

## Troubleshooting

### Database Issues
- Tests use SQLite in-memory database
- Each test function gets a fresh database session
- Transactions are rolled back after each test

### Async Issues
- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` decorator
- Check event loop configuration in conftest.py

### Import Issues
- Run tests from the `apps/api` directory
- Ensure `__init__.py` files exist in all test directories
- Check PYTHONPATH if imports fail 