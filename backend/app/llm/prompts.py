"""
XML Prompt Management Module

This module provides functionality to load, parse, and manage XML-formatted prompts
for use with the MCP (Model Context Protocol) system.
"""

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Optional, List
from pathlib import Path

class XMLParseError(Exception):
    """Exception raised for errors during XML prompt parsing."""
    pass

@dataclass
class PromptTemplate:
    """Represents a parsed prompt template with metadata."""
    name: str
    content: str
    variables: Dict[str, str]
    description: Optional[str] = None
    examples: List[Dict[str, str]] = None

    def format(self, **kwargs) -> str:
        """Format the prompt template with provided variables."""
        try:
            return self.content.format(**{**self.variables, **kwargs})
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")

class PromptManager:
    """Manages loading and handling of XML prompt templates."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_prompts()

    def _load_prompts(self):
        """Load all XML prompts from the prompts directory."""
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")

        for xml_file in self.prompts_dir.glob("*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Extract basic metadata
                name = xml_file.stem
                content = root.find("content").text.strip() if root.find("content") is not None else ""
                description = root.find("description")
                description_text = description.text.strip() if description is not None else None
                
                # Extract variables
                variables = {}
                vars_elem = root.find("variables")
                if vars_elem is not None:
                    for var in vars_elem.findall("variable"):
                        var_name = var.get("name")
                        var_default = var.get("default", "")
                        variables[var_name] = var_default
                
                # Extract examples
                examples = []
                examples_elem = root.find("examples")
                if examples_elem is not None:
                    for example in examples_elem.findall("example"):
                        example_data = {
                            "input": example.find("input").text.strip(),
                            "output": example.find("output").text.strip()
                        }
                        examples.append(example_data)
                
                template = PromptTemplate(
                    name=name,
                    content=content,
                    variables=variables,
                    description=description_text,
                    examples=examples
                )
                self.templates[name] = template
                
            except ET.ParseError as e:
                raise XMLParseError(f"Error parsing {xml_file}: {e}")

    def get_prompt(self, name: str) -> PromptTemplate:
        """Retrieve a prompt template by name."""
        if name not in self.templates:
            raise KeyError(f"Prompt template not found: {name}")
        return self.templates[name]

    def format_prompt(self, name: str, **kwargs) -> str:
        """Format a prompt template with provided variables."""
        template = self.get_prompt(name)
        return template.format(**kwargs)

    def list_prompts(self) -> List[str]:
        """List all available prompt templates."""
        return list(self.templates.keys())

    def reload_prompts(self):
        """Reload all prompt templates from disk."""
        self.templates.clear()
        self._load_prompts()

# Initialize global prompt manager instance
prompt_manager = PromptManager()

