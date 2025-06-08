#!/usr/bin/env python3
"""
Prisma to SQLAlchemy Model Generator

This script parses a Prisma schema file and generates corresponding SQLAlchemy models.
It maintains compatibility with the Prisma schema structure while adapting to SQLAlchemy patterns.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PrismaEnum:
    """Represents a Prisma enum"""
    name: str
    values: List[str]


@dataclass
class PrismaField:
    """Represents a field in a Prisma model"""
    name: str
    type: str
    is_optional: bool = False
    is_array: bool = False
    is_unique: bool = False
    is_id: bool = False
    default_value: Optional[str] = None
    attributes: List[str] = field(default_factory=list)
    db_type: Optional[str] = None
    relation_model: Optional[str] = None
    relation_fields: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


@dataclass
class PrismaModel:
    """Represents a Prisma model"""
    name: str
    fields: List[PrismaField]
    indexes: List[List[str]] = field(default_factory=list)
    unique_constraints: List[List[str]] = field(default_factory=list)
    table_map: Optional[str] = None


class PrismaSchemaParser:
    """Parses Prisma schema files"""
    
    def __init__(self, schema_content: str):
        self.schema_content = schema_content
        self.models: Dict[str, PrismaModel] = {}
        self.enums: Dict[str, PrismaEnum] = {}
        
    def parse(self) -> Tuple[Dict[str, PrismaModel], Dict[str, PrismaEnum]]:
        """Parse the schema and return models and enums"""
        self._parse_enums()
        self._parse_models()
        return self.models, self.enums
    
    def _parse_enums(self):
        """Parse enum definitions"""
        enum_pattern = r'enum\s+(\w+)\s*{([^}]+)}'
        for match in re.finditer(enum_pattern, self.schema_content, re.MULTILINE | re.DOTALL):
            enum_name = match.group(1)
            enum_body = match.group(2)
            values = []
            for line in enum_body.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('//'):
                    # Remove inline comments
                    value = line.split('//')[0].strip()
                    if value:
                        values.append(value)
            self.enums[enum_name] = PrismaEnum(name=enum_name, values=values)
    
    def _parse_models(self):
        """Parse model definitions"""
        model_pattern = r'model\s+(\w+)\s*{([^}]+)}'
        for match in re.finditer(model_pattern, self.schema_content, re.MULTILINE | re.DOTALL):
            model_name = match.group(1)
            model_body = match.group(2)
            
            model = PrismaModel(name=model_name, fields=[])
            
            # Parse fields
            field_lines = []
            current_line = ""
            for line in model_body.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                    
                # Handle multi-line fields
                if line.startswith('@@'):
                    self._parse_model_attribute(model, line)
                elif not line.startswith('@') or current_line:
                    current_line += " " + line if current_line else line
                    if not line.endswith(']') or line.count('[') == line.count(']'):
                        field_lines.append(current_line.strip())
                        current_line = ""
                else:
                    field_lines.append(line)
            
            # Parse each field
            for field_line in field_lines:
                if field_line and not field_line.startswith('@@'):
                    field = self._parse_field(field_line)
                    if field:
                        model.fields.append(field)
            
            self.models[model_name] = model
    
    def _parse_field(self, field_line: str) -> Optional[PrismaField]:
        """Parse a single field definition"""
        # Skip comments and model attributes
        if field_line.startswith('//') or field_line.startswith('@@'):
            return None
            
        # Basic field pattern: name Type modifiers @attributes
        field_pattern = r'^(\w+)\s+(\w+)(\[\])?(\?)?\s*(.*)?$'
        match = re.match(field_pattern, field_line)
        
        if not match:
            return None
            
        field_name = match.group(1)
        field_type = match.group(2)
        is_array = bool(match.group(3))
        is_optional = bool(match.group(4))
        attributes_str = match.group(5) or ""
        
        field = PrismaField(
            name=field_name,
            type=field_type,
            is_array=is_array,
            is_optional=is_optional
        )
        
        # Parse attributes
        if attributes_str:
            # Extract @relation
            relation_match = re.search(r'@relation\(([^)]+)\)', attributes_str)
            if relation_match:
                relation_content = relation_match.group(1)
                # Parse fields
                fields_match = re.search(r'fields:\s*\[([^\]]+)\]', relation_content)
                if fields_match:
                    field.relation_fields = [f.strip() for f in fields_match.group(1).split(',')]
                # Parse references
                refs_match = re.search(r'references:\s*\[([^\]]+)\]', relation_content)
                if refs_match:
                    field.references = [r.strip() for r in refs_match.group(1).split(',')]
                field.relation_model = field_type
            
            # Extract other attributes
            field.is_id = '@id' in attributes_str
            field.is_unique = '@unique' in attributes_str
            
            # Extract default - handle parentheses properly
            default_match = re.search(r'@default\(([^)]+\)|[^)]+)\)', attributes_str)
            if default_match:
                field.default_value = default_match.group(1)
            
            # Extract db type
            db_match = re.search(r'@db\.(\w+)(?:\(([^)]+)\))?', attributes_str)
            if db_match:
                field.db_type = db_match.group(1)
                if db_match.group(2):
                    field.db_type += f"({db_match.group(2)})"
        
        return field
    
    def _parse_model_attribute(self, model: PrismaModel, line: str):
        """Parse model-level attributes like @@index, @@unique, @@map"""
        if line.startswith('@@index'):
            index_match = re.search(r'@@index\(\[([^\]]+)\]\)', line)
            if index_match:
                fields = [f.strip() for f in index_match.group(1).split(',')]
                model.indexes.append(fields)
        elif line.startswith('@@unique'):
            unique_match = re.search(r'@@unique\(\[([^\]]+)\]\)', line)
            if unique_match:
                fields = [f.strip() for f in unique_match.group(1).split(',')]
                model.unique_constraints.append(fields)
        elif line.startswith('@@map'):
            map_match = re.search(r'@@map\("([^"]+)"\)', line)
            if map_match:
                model.table_map = map_match.group(1)


class SQLAlchemyGenerator:
    """Generates SQLAlchemy models from parsed Prisma schema"""
    
    # Type mappings from Prisma to SQLAlchemy
    TYPE_MAPPINGS = {
        'String': 'String',
        'Int': 'Integer',
        'BigInt': 'BigInteger',
        'Float': 'Float',
        'Decimal': 'Numeric',
        'Boolean': 'Boolean',
        'DateTime': 'DateTime',
        'Json': 'JSON',
        'Bytes': 'LargeBinary',
    }
    
    def __init__(self, models: Dict[str, PrismaModel], enums: Dict[str, PrismaEnum]):
        self.models = models
        self.enums = enums
        self.imports: Set[str] = set()
        self.has_func_default = False
        
    def generate(self) -> str:
        """Generate the complete SQLAlchemy models file"""
        self._collect_imports()
        
        output = []
        
        # Header
        output.append('"""')
        output.append('SQLAlchemy models generated from Prisma schema')
        output.append(f'Generated at: {datetime.now().isoformat()}')
        output.append('"""')
        output.append('')
        
        # Imports
        output.append('from datetime import datetime')
        output.append('from decimal import Decimal')
        output.append('from typing import Optional, List')
        output.append('import enum')
        output.append('')
        output.append('from sqlalchemy import (')
        imports_list = sorted(list(self.imports))
        for imp in imports_list[:-1]:
            output.append(f'    {imp},')
        output.append(f'    {imports_list[-1]}')
        output.append(')')
        if self.has_func_default:
            output.append('from sqlalchemy.sql import func')
        output.append('from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship')
        output.append('from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID')
        output.append('')
        output.append('')
        
        # Base class
        output.append('class Base(DeclarativeBase):')
        output.append('    """Base class for all models"""')
        output.append('    pass')
        output.append('')
        output.append('')
        
        # Generate enums
        for enum_name, enum_def in sorted(self.enums.items()):
            output.extend(self._generate_enum(enum_def))
            output.append('')
        
        # Generate models
        for model_name, model in sorted(self.models.items()):
            output.extend(self._generate_model(model))
            output.append('')
        
        return '\n'.join(output)
    
    def _collect_imports(self):
        """Collect all necessary imports based on field types"""
        self.imports.add('Column')
        self.imports.add('String')
        self.imports.add('Integer')
        self.imports.add('Boolean')
        self.imports.add('DateTime')
        self.imports.add('ForeignKey')
        self.imports.add('Table')
        self.imports.add('Index')
        self.imports.add('UniqueConstraint')
        
        # Check for specific types
        for model in self.models.values():
            for field in model.fields:
                if field.type == 'Decimal' or field.db_type and 'Decimal' in field.db_type:
                    self.imports.add('Numeric')
                if field.type == 'BigInt':
                    self.imports.add('BigInteger')
                if field.type == 'Float':
                    self.imports.add('Float')
                if field.type == 'Bytes':
                    self.imports.add('LargeBinary')
                if field.type in self.enums:
                    self.imports.add('Enum')
                if field.default_value == 'now()':
                    self.has_func_default = True
    
    def _generate_enum(self, enum_def: PrismaEnum) -> List[str]:
        """Generate Python enum class"""
        output = []
        output.append(f'class {enum_def.name}(enum.Enum):')
        output.append(f'    """Generated from Prisma enum {enum_def.name}"""')
        for value in enum_def.values:
            output.append(f'    {value} = "{value}"')
        return output
    
    def _generate_model(self, model: PrismaModel) -> List[str]:
        """Generate SQLAlchemy model class"""
        output = []
        
        # Class definition
        output.append(f'class {model.name}(Base):')
        output.append(f'    """Generated from Prisma model {model.name}"""')
        
        # Table name
        table_name = model.table_map or self._to_snake_case(model.name)
        output.append(f'    __tablename__ = "{table_name}"')
        output.append('')
        
        # Generate fields
        for field in model.fields:
            field_lines = self._generate_field(field, model)
            output.extend(field_lines)
        
        # Generate table arguments (indexes, constraints)
        table_args = self._generate_table_args(model)
        if table_args:
            output.append('')
            output.append('    __table_args__ = (')
            if len(table_args) == 1:
                output.append(f'        {table_args[0]},')
            else:
                for arg in table_args[:-1]:
                    output.append(f'        {arg},')
                output.append(f'        {table_args[-1]}')
            output.append('    )')
        
        return output
    
    def _generate_field(self, field: PrismaField, model: PrismaModel) -> List[str]:
        """Generate field definition"""
        output = []
        
        # Skip relation fields that don't have actual columns
        if field.type in self.models and not field.relation_fields:
            # This is a relation field without FK
            output.append(f'    # {field.name}: Mapped["{field.type}"] = relationship(back_populates="{self._find_back_populates(model.name, field.type)}")')
            return output
        
        # Determine SQLAlchemy type
        sa_type = self._get_sqlalchemy_type(field)
        
        # Build column definition
        column_args = []
        
        # Primary key
        if field.is_id:
            column_args.append('primary_key=True')
        
        # Foreign key
        if field.relation_fields:
            # This field is referenced by a relation
            for i, rel_field in enumerate(field.relation_fields):
                fk_model = field.relation_model
                fk_table = self._to_snake_case(fk_model)
                fk_column = self._to_snake_case(field.references[i] if i < len(field.references) else 'id')
                column_args.append(f'ForeignKey("{fk_table}.{fk_column}")')
        
        # Unique
        if field.is_unique:
            column_args.append('unique=True')
        
        # Nullable
        if field.is_optional and not field.is_id:
            column_args.append('nullable=True')
        else:
            column_args.append('nullable=False')
        
        # Default values
        if field.default_value:
            default = self._convert_default_value(field.default_value)
            if default:
                column_args.append(f'default={default}')
        
        # Index
        if any(field.name in idx for idx in model.indexes):
            column_args.append('index=True')
        
        # Build the field line
        field_name = self._to_snake_case(field.name)
        
        # Handle reserved names
        if field_name in ['metadata']:
            field_name = field_name + '_'
        
        if column_args:
            args_str = ', '.join(column_args)
            output.append(f'    {field_name}: Mapped[{self._get_python_type(field)}] = mapped_column({sa_type}, {args_str})')
        else:
            output.append(f'    {field_name}: Mapped[{self._get_python_type(field)}] = mapped_column({sa_type})')
        
        return output
    
    def _get_sqlalchemy_type(self, field: PrismaField) -> str:
        """Get SQLAlchemy type for a Prisma field"""
        # Handle special DB types
        if field.db_type:
            if 'Decimal' in field.db_type:
                return field.db_type.replace('Decimal', 'Numeric')
            elif field.db_type == 'Text':
                return 'Text'
        
        # Handle arrays
        if field.is_array:
            inner_type = self.TYPE_MAPPINGS.get(field.type, 'String')
            return f'ARRAY({inner_type})'
        
        # Handle enums
        if field.type in self.enums:
            return f'Enum({field.type})'
        
        # Handle foreign keys
        if field.type in self.models:
            # This is a relation, return the ID type
            return 'String'  # Assuming CUID/UUID strings
        
        # Standard type mapping
        return self.TYPE_MAPPINGS.get(field.type, 'String')
    
    def _get_python_type(self, field: PrismaField) -> str:
        """Get Python type hint for a field"""
        python_types = {
            'String': 'str',
            'Int': 'int',
            'BigInt': 'int',
            'Float': 'float',
            'Decimal': 'Decimal',
            'Boolean': 'bool',
            'DateTime': 'datetime',
            'Json': 'dict',
            'Bytes': 'bytes',
        }
        
        if field.is_array:
            base_type = python_types.get(field.type, 'str')
            type_str = f'List[{base_type}]'
        elif field.type in self.enums:
            type_str = field.type
        elif field.type in self.models:
            type_str = 'str'  # Foreign key
        else:
            type_str = python_types.get(field.type, 'str')
        
        if field.is_optional:
            return f'Optional[{type_str}]'
        return type_str
    
    def _convert_default_value(self, default: str) -> Optional[str]:
        """Convert Prisma default to SQLAlchemy default"""
        if default == 'now()':
            self.has_func_default = True  # Set flag to import func
            return 'func.now()'
        elif default in ['cuid()', 'uuid()']:
            return None  # Handle in application
        elif default == 'true':
            return 'True'
        elif default == 'false':
            return 'False'
        elif default.startswith('"') and default.endswith('"'):
            return default  # String literal
        elif default.isdigit():
            return default
        elif default in ['[]', '{}']:
            return default
        else:
            # Check if it's a numeric value with decimals
            try:
                float(default)
                return default
            except ValueError:
                return f'"{default}"'
    
    def _generate_table_args(self, model: PrismaModel) -> List[str]:
        """Generate table arguments for indexes and constraints"""
        args = []
        
        # Composite indexes
        for idx_fields in model.indexes:
            if len(idx_fields) > 1:
                fields_str = ', '.join(f'"{self._to_snake_case(f)}"' for f in idx_fields)
                args.append(f'Index("idx_{model.name.lower()}_{"_".join(idx_fields)}", {fields_str})')
        
        # Unique constraints
        for unique_fields in model.unique_constraints:
            fields_str = ', '.join(f'"{self._to_snake_case(f)}"' for f in unique_fields)
            args.append(f'UniqueConstraint({fields_str})')
        
        return args
    
    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase/camelCase to snake_case"""
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _find_back_populates(self, from_model: str, to_model: str) -> str:
        """Find the back_populates field name"""
        # Look for a field in to_model that references from_model
        if to_model in self.models:
            for field in self.models[to_model].fields:
                if field.type == from_model or field.relation_model == from_model:
                    return field.name
        return from_model.lower()


def main():
    """Main entry point"""
    if len(sys.argv) != 3:
        print("Usage: python generator.py <prisma_schema_path> <output_path>")
        sys.exit(1)
    
    schema_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)
    
    # Read schema
    schema_content = schema_path.read_text()
    
    # Parse schema
    parser = PrismaSchemaParser(schema_content)
    models, enums = parser.parse()
    
    print(f"Parsed {len(models)} models and {len(enums)} enums")
    
    # Generate SQLAlchemy models
    generator = SQLAlchemyGenerator(models, enums)
    output = generator.generate()
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output)
    
    print(f"Generated SQLAlchemy models to: {output_path}")


if __name__ == "__main__":
    main() 