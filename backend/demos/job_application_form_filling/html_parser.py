"""
HTML Form Parser
================

Parses HTML to discover form structure dynamically.
"""

import logging
from typing import List, Optional
from bs4 import BeautifulSoup
from .models import FormField, FormStructure

logger = logging.getLogger(__name__)


def parse_html_form(html_content: str) -> FormStructure:
    """
    Parse HTML content to discover form structure.
    
    This function extracts all form fields from HTML, including:
    - Input fields (text, email, tel, etc.)
    - Textarea fields
    - Select/dropdown fields
    - Field labels, names, types, and sections
    
    Args:
        html_content: HTML content as string
        
    Returns:
        FormStructure with discovered fields
    """
    try:
        logger.info("Starting HTML form parsing...")
        logger.debug(f"HTML content length: {len(html_content)} characters")
        logger.debug(f"HTML preview (first 500 chars): {html_content[:500]}")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all form elements
        forms = soup.find_all('form')
        if not forms:
            logger.warning("No <form> tags found in HTML, searching for input fields directly")
            # If no form tag, look for inputs directly in the entire document
            form_element = soup
        else:
            # Use the first form (or combine all forms)
            form_element = forms[0]
            logger.info(f"Found {len(forms)} form(s), using first form")
        
        fields: List[FormField] = []
        sections: List[str] = []
        seen_sections = set()
        
        # Find all input fields - be more aggressive in finding them
        inputs = form_element.find_all(['input', 'textarea', 'select'])
        logger.info(f"Found {len(inputs)} form fields (input/textarea/select)")
        
        # If no inputs found, try to find any element with form-related attributes
        if not inputs:
            logger.warning("No standard form fields found, searching for elements with form attributes...")
            # Look for divs or other elements that might contain form fields
            potential_fields = form_element.find_all(attrs={'name': True}) + form_element.find_all(attrs={'id': True})
            logger.info(f"Found {len(potential_fields)} potential form elements with name/id attributes")
            inputs = [elem for elem in potential_fields if elem.name in ['input', 'textarea', 'select']]
        
        # Log what we found
        if inputs:
            logger.info(f"Processing {len(inputs)} form fields")
            for inp in inputs[:5]:  # Log first 5
                logger.debug(f"  - {inp.name} with name={inp.get('name')} id={inp.get('id')} type={inp.get('type')}")
        else:
            logger.error("No form fields found at all!")
            logger.debug(f"HTML structure: {str(soup)[:1000]}")
        
        for input_elem in inputs:
            try:
                # Get field name
                name = input_elem.get('name') or input_elem.get('id') or ''
                if not name:
                    logger.debug(f"Skipping field without name/id: {input_elem}")
                    continue
                
                # Get field type
                field_type = input_elem.get('type', 'text').lower()
                if input_elem.name == 'textarea':
                    field_type = 'textarea'
                elif input_elem.name == 'select':
                    field_type = 'select'
                
                # Get label - try multiple methods
                label = ''
                label_elem = None
                
                # Method 1: Associated label via 'for' attribute
                label_id = input_elem.get('id')
                if label_id:
                    label_elem = form_element.find('label', {'for': label_id})
                
                # Method 2: Parent label
                if not label_elem:
                    parent = input_elem.parent
                    if parent and parent.name == 'label':
                        label_elem = parent
                
                # Method 3: Previous sibling label
                if not label_elem:
                    prev = input_elem.find_previous_sibling('label')
                    if prev:
                        label_elem = prev
                
                # Method 4: Placeholder as fallback
                if not label_elem:
                    placeholder = input_elem.get('placeholder', '')
                    if placeholder:
                        label = placeholder
                
                if label_elem:
                    label = label_elem.get_text(strip=True)
                
                # If still no label, use name
                if not label:
                    label = name.replace('_', ' ').replace('-', ' ').title()
                
                # Determine section - look for parent section/div with class/id containing 'section'
                section = 'General'
                parent = input_elem.parent
                depth = 0
                while parent and depth < 5:  # Limit depth to avoid going too far up
                    parent_class = parent.get('class', [])
                    parent_id = parent.get('id', '')
                    parent_tag = parent.name.lower()
                    
                    # Check for section indicators
                    section_keywords = ['section', 'fieldset', 'group', 'panel', 'card']
                    if any(keyword in str(parent_class).lower() or keyword in str(parent_id).lower() for keyword in section_keywords):
                        # Try to get section title
                        section_title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'legend'])
                        if section_title_elem:
                            section = section_title_elem.get_text(strip=True)
                            break
                        elif parent_id:
                            section = parent_id.replace('-', ' ').replace('_', ' ').title()
                            break
                        elif parent_class:
                            section = str(parent_class[0]).replace('-', ' ').replace('_', ' ').title()
                            break
                    
                    if parent_tag in ['section', 'fieldset']:
                        section_title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'legend'])
                        if section_title_elem:
                            section = section_title_elem.get_text(strip=True)
                            break
                    
                    parent = parent.parent
                    depth += 1
                
                # Check if required
                required = (
                    input_elem.get('required') is not None or
                    input_elem.has_attr('required') or
                    'required' in str(input_elem.get('class', [])).lower()
                )
                
                field = FormField(
                    name=name,
                    label=label,
                    type=field_type,
                    section=section,
                    required=required
                )
                
                fields.append(field)
                
                # Track sections
                if section not in seen_sections:
                    seen_sections.add(section)
                    sections.append(section)
                
                logger.debug(f"Parsed field: {name} ({field_type}) in section '{section}'")
                
            except Exception as e:
                logger.warning(f"Error parsing field {input_elem}: {e}")
                continue
        
        if not fields:
            logger.error("No fields found in HTML form after parsing")
            logger.error(f"HTML had {len(inputs)} input/textarea/select elements but none were parsed")
            logger.debug(f"Sample HTML structure: {str(soup)[:2000]}")
            # Return a default structure
            return FormStructure(
                sections=["General"],
                fields=[]
            )
        
        logger.info(f"Successfully parsed {len(fields)} fields in {len(sections)} sections")
        
        return FormStructure(
            sections=sections,
            fields=fields
        )
        
    except Exception as e:
        logger.error(f"Error parsing HTML form: {e}", exc_info=True)
        # Return empty structure on error
        return FormStructure(
            sections=["General"],
            fields=[]
        )

