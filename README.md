# Wedi Pay

AI-native payment orchestration platform for cross-border payments in Latin America.

## Overview

Wedi Pay is a modern payment infrastructure platform that simplifies cross-border transactions between Colombia and Mexico. Built with AI at its core, it provides intelligent payment routing, multi-currency support, and seamless integration with local payment providers.

## Architecture

This monorepo is organized using Turborepo and contains:

- **apps/web**: Next.js frontend application
- **apps/api**: FastAPI backend with Python
- **packages/shared**: Shared utilities and types
- **packages/database**: Database models and migrations
- **packages/ui**: Shared UI components
- **config**: Shared configuration files

## Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript, TailwindCSS, Radix UI
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy, Alembic
- **Database**: PostgreSQL with multi-tenancy support
- **Message Queue**: Kafka (Redpanda Cloud)
- **Cache**: Redis
- **Authentication**: Thirdweb Auth (with automatic wallet creation)
- **Payment Providers**: Yoint (Colombia), Trubit/Prometeo (Mexico)

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Poetry (Python package manager)
- PostgreSQL 14+
- Redis
- Docker (optional, for local services)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wedi.git
cd wedi
```

2. Install dependencies:
```bash
# Install Node.js dependencies
npm install

# Install Python dependencies for the API
cd apps/api
poetry install
cd ../..
```

3. Set up environment variables:
```bash
# Copy example env files
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
# Edit the .env files with your configuration
```

4. Set up the database:
```bash
# Run from apps/api directory
cd apps/api
poetry run alembic upgrade head
cd ../..
```

### Development

Run all services in development mode:
```bash
npm run dev
```

This will start:
- Next.js frontend on http://localhost:3000
- FastAPI backend on http://localhost:8000
- API documentation on http://localhost:8000/api/docs

### Running Individual Services

```bash
# Frontend only
npm run dev --filter=@wedi/web

# Backend only
npm run dev --filter=@wedi/api

# Or directly with Poetry
cd apps/api
poetry run uvicorn app.main:app --reload
```

## Project Structure

```
wedi/
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/          # FastAPI backend
├── packages/
│   ├── shared/       # Shared utilities
│   ├── database/     # Database models
│   └── ui/          # Shared UI components
├── config/
│   ├── eslint-config/
│   └── typescript-config/
├── turbo.json       # Turborepo configuration
└── package.json     # Root package.json
```

## Available Scripts

- `npm run build` - Build all packages
- `npm run dev` - Start development servers
- `npm run lint` - Lint all packages
- `npm run test` - Run tests
- `npm run format` - Format code with Prettier

## Contributing

Please read our contributing guidelines before submitting PRs.

## License

This project is licensed under the MIT License. 