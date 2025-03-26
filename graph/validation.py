import re
import ast
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum
from dataclasses import dataclass, asdict, field
import networkx as nx
import matplotlib.pyplot as plt

class SchemaValidationSeverity(Enum):
    """Categorize validation issue severity"""
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

@dataclass
class ValidationIssue:
    """Represents a single schema validation finding"""
    message: str
    severity: SchemaValidationSeverity
    location: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

class AdvancedSchemaValidator:
    """
    Comprehensive schema validation framework with advanced capabilities
    
    Design Principles:
    - Deep type introspection
    - Multi-schema compatibility analysis
    - Semantic type relationship mapping
    - Extensible validation infrastructure
    """
    
    def __init__(self, 
                 python_schema_paths: List[str], 
                 graphql_schema_paths: List[str],
                 strict_mode: bool = False):
        """
        Initialize validator with multiple schema sources
        
        Args:
            python_schema_paths (List[str]): Paths to Python schema files
            graphql_schema_paths (List[str]): Paths to GraphQL schema files
            strict_mode (bool): Enables more rigorous validation
        """
        self.python_schema_paths = python_schema_paths
        self.graphql_schema_paths = graphql_schema_paths
        self.strict_mode = strict_mode
        
        self.validation_issues: List[ValidationIssue] = []
        self.type_graph = nx.DiGraph()
        
        # Advanced logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d]: %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('schema_validation.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _advanced_python_type_parsing(self, file_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Advanced Python type parsing with AST
        Supports:
        - Nested type definitions
        - Type hints
        - Generics
        
        Args:
            file_path (str): Path to Python schema file
        
        Returns:
            Comprehensive type definitions dictionary
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        module = ast.parse(content)
        type_definitions = {}
        
        class TypeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.types = {}
            
            def visit_ClassDef(self, node: ast.ClassDef):
                """
                Extract detailed class type information
                """
                class_info = {
                    'name': node.name,
                    'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
                    'fields': {},
                    'docstring': ast.get_docstring(node) or ''
                }
                
                for body_node in node.body:
                    if isinstance(body_node, ast.AnnAssign):
                        # Handle type annotations
                        if isinstance(body_node.target, ast.Name):
                            field_name = body_node.target.id
                            
                            # Extract type annotation details
                            if isinstance(body_node.annotation, ast.Name):
                                field_type = body_node.annotation.id
                            elif isinstance(body_node.annotation, ast.Subscript):
                                # Handle generic types like List[str], Dict[str, int]
                                field_type = self._parse_subscript_type(body_node.annotation)
                            else:
                                field_type = str(body_node.annotation)
                            
                            class_info['fields'][field_name] = {
                                'type': field_type,
                                'optional': isinstance(body_node.value, (ast.Constant, type(None)))
                            }
                
                self.types[node.name] = class_info
            
            def _parse_subscript_type(self, annotation: ast.Subscript) -> str:
                """
                Parse complex type annotations
                """
                if isinstance(annotation.value, ast.Name):
                    container = annotation.value.id
                    
                    # Handle type arguments
                    if isinstance(annotation.slice, ast.Index):
                        slice_value = annotation.slice.value
                    elif isinstance(annotation.slice, ast.Tuple):
                        slice_value = annotation.slice.elts
                    else:
                        slice_value = annotation.slice
                    
                    if isinstance(slice_value, ast.Name):
                        return f"{container}[{slice_value.id}]"
                    elif isinstance(slice_value, list):
                        type_args = ', '.join(arg.id for arg in slice_value if isinstance(arg, ast.Name))
                        return f"{container}[{type_args}]"
                
                return str(annotation)
        
        visitor = TypeVisitor()
        visitor.visit(module)
        
        return visitor.types

    def _advanced_graphql_type_parsing(self, file_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Advanced GraphQL schema parsing with regex and semantic analysis
        
        Args:
            file_path (str): Path to GraphQL schema file
        
        Returns:
            Comprehensive type definitions dictionary
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Enhanced type and field parsing
        type_pattern = re.compile(r'type\s+(\w+)\s*{([^}]*)}', re.DOTALL)
        field_pattern = re.compile(r'\s*(\w+):\s*([^!,\n]+)(!|\[.*?\])?')
        
        type_definitions = {}
        
        for type_match in type_pattern.finditer(content):
            type_name = type_match.group(1)
            fields_content = type_match.group(2)
            
            fields = {}
            for field_match in field_pattern.finditer(fields_content):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                is_required = field_match.group(3) == '!'
                
                fields[field_name] = {
                    'type': field_type,
                    'required': is_required
                }
            
            type_definitions[type_name] = {
                'name': type_name,
                'fields': fields
            }
        
        return type_definitions

    def validate_type_compatibility(self) -> List[ValidationIssue]:
        """
        Comprehensive type compatibility validation
        
        Returns:
            List of validation issues across multiple schema sources
        """
        issues = []
        
        # Aggregate types from all schema sources
        python_types = {}
        for path in self.python_schema_paths:
            python_types.update(self._advanced_python_type_parsing(path))
        
        graphql_types = {}
        for path in self.graphql_schema_paths:
            graphql_types.update(self._advanced_graphql_type_parsing(path))
        
        # Cross-reference and validate type definitions
        for type_name, python_def in python_types.items():
            if type_name not in graphql_types:
                issues.append(ValidationIssue(
                    message=f"Type '{type_name}' missing in GraphQL schema",
                    severity=SchemaValidationSeverity.WARNING,
                    location='Python Schema',
                    details={'python_type': python_def}
                ))
            else:
                graphql_def = graphql_types[type_name]
                
                # Compare fields
                for field_name, python_field in python_def.get('fields', {}).items():
                    if field_name not in graphql_def['fields']:
                        issues.append(ValidationIssue(
                            message=f"Field '{field_name}' missing in GraphQL type '{type_name}'",
                            severity=SchemaValidationSeverity.WARNING,
                            location='Python Schema',
                            details={
                                'field_name': field_name,
                                'python_field_type': python_field
                            }
                        ))
        
        return issues

    def generate_type_relationship_graph(self):
        """
        Create a graph visualization of type relationships
        """
        for type_name, type_def in self._advanced_python_type_parsing(self.python_schema_paths[0]).items():
            # Add nodes for types
            self.type_graph.add_node(type_name)
            
            # Add edges for base classes and field types
            for base in type_def.get('bases', []):
                self.type_graph.add_edge(base, type_name)
            
            for field_name, field_info in type_def.get('fields', {}).items():
                field_type = field_info['type']
                self.type_graph.add_edge(type_name, field_type)
        
        # Visualize the graph
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.type_graph)
        nx.draw(self.type_graph, pos, with_labels=True, node_color='lightblue', 
                node_size=1500, font_size=8, font_weight='bold')
        plt.title("Type Relationship Graph")
        plt.tight_layout()
        plt.savefig('type_relationship_graph.png')
        plt.close()

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Execute full schema validation pipeline
        
        Returns:
            Comprehensive validation report
        """
        validation_start_time = datetime.now()
        
        # Reset validation state
        self.validation_issues = []
        self.type_graph.clear()
        
        # Run validation modules
        type_compatibility_issues = self.validate_type_compatibility()
        
        # Aggregate issues
        self.validation_issues.extend(type_compatibility_issues)
        
        # Generate type relationship visualization
        self.generate_type_relationship_graph()
        
        # Prepare detailed validation report
        report = {
            'timestamp': validation_start_time.isoformat(),
            'total_issues': len(self.validation_issues),
            'severity_breakdown': {
                severity.name: sum(1 for issue in self.validation_issues if issue.severity == severity)
                for severity in SchemaValidationSeverity
            },
            'issues': [asdict(issue) for issue in self.validation_issues],
            'validation_duration': (datetime.now() - validation_start_time).total_seconds(),
            'type_graph_visualization': 'type_relationship_graph.png'
        }
        
        # Log findings
        if self.validation_issues:
            self.logger.warning(f"Schema validation found {len(self.validation_issues)} issues")
            for issue in self.validation_issues:
                self.logger.log(
                    {
                        SchemaValidationSeverity.INFO: logging.INFO,
                        SchemaValidationSeverity.WARNING: logging.WARNING,
                        SchemaValidationSeverity.ERROR: logging.ERROR,
                        SchemaValidationSeverity.CRITICAL: logging.CRITICAL
                    }[issue.severity],
                    f"{issue.severity.name}: {issue.message}"
                )
        else:
            self.logger.info("Schema validation completed successfully")
        
        return report

def main():
    """
    Demonstrate advanced schema validation
    """
    validator = AdvancedSchemaValidator(
        python_schema_paths=['schema/schema.py'],
        graphql_schema_paths=['schema/schema.graphql'],
        strict_mode=True
    )
    
    validation_report = validator.run_comprehensive_validation()
    
    # Pretty print validation report
    print(json.dumps(validation_report, indent=2))

if __name__ == '__main__':
    main()
