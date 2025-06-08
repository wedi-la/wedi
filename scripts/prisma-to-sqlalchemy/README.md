# Prisma to SQLAlchemy Model Generator

This tool automatically generates SQLAlchemy models from a Prisma schema file to maintain consistency between TypeScript (Prisma) and Python (FastAPI) parts of the application.

## Overview

Since the Wedi platform uses:
- **Prisma** as the primary ORM and source of truth for database schema
- **FastAPI** with SQLAlchemy for the Python backend

We need to keep both model definitions in sync. This generator automates that process.

## Usage

### Generate Models

```bash
python scripts/prisma-to-sqlalchemy/generator.py packages/prisma/schema.prisma apps/api/app/models/generated.py
```

### Validate Generated Models

```bash
python scripts/prisma-to-sqlalchemy/validate_models.py apps/api/app/models/generated.py
```

## Features

- **Automatic Type Mapping**: Converts Prisma types to SQLAlchemy equivalents
- **Enum Generation**: Creates Python enums from Prisma enums
- **Relationship Handling**: Properly handles foreign keys and relationships
- **Index & Constraint Support**: Generates composite indexes and unique constraints
- **Reserved Word Handling**: Automatically renames reserved SQLAlchemy fields (e.g., `metadata` → `metadata_`)
- **Default Value Conversion**: Converts Prisma defaults to SQLAlchemy equivalents

## Type Mappings

| Prisma Type | SQLAlchemy Type |
|-------------|----------------|
| String | String |
| Int | Integer |
| BigInt | BigInteger |
| Float | Float |
| Decimal | Numeric |
| Boolean | Boolean |
| DateTime | DateTime |
| Json | JSON |
| Bytes | LargeBinary |
| Array | ARRAY |

## Limitations

1. **CUID/UUID Generation**: Prisma's `@default(cuid())` is not directly supported. Handle ID generation in application code.
2. **Complex Relations**: Many-to-many relationships through join tables need manual adjustment
3. **Prisma-specific Features**: Some Prisma features like `@map` for field names require special handling

## Workflow

1. Make changes to `packages/prisma/schema.prisma`
2. Run Prisma migration: `npx prisma migrate dev`
3. Regenerate SQLAlchemy models: `python scripts/prisma-to-sqlalchemy/generator.py ...`
4. Validate the generated models: `python scripts/prisma-to-sqlalchemy/validate_models.py ...`
5. Commit both the Prisma schema changes and the regenerated SQLAlchemy models

## CI/CD Integration

Add these steps to your CI pipeline to ensure models stay in sync:

```yaml
- name: Generate SQLAlchemy Models
  run: python scripts/prisma-to-sqlalchemy/generator.py packages/prisma/schema.prisma apps/api/app/models/generated.py

- name: Check for Model Changes
  run: |
    if [[ `git status --porcelain` ]]; then
      echo "SQLAlchemy models are out of sync with Prisma schema!"
      exit 1
    fi
```

## Architecture Decision

We chose code generation over:
- **Manual Synchronization**: Too error-prone and time-consuming
- **Prisma Client Python**: Deprecated and not suitable for production
- **Single ORM**: Need both TypeScript and Python support

This approach ensures type safety and consistency while maintaining the flexibility to use the best tools for each part of the stack. 