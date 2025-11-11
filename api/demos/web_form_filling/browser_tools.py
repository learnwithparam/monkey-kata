"""
Browser Automation Tools
========================

🎯 LEARNING OBJECTIVES:
This module teaches you how to create browser automation tools:

1. Playwright Integration - How to control a browser programmatically
2. Form Detection - How to identify form fields on a page
3. Form Filling - How to fill form fields automatically
4. Tool Wrapping - How to wrap browser actions as agent tools

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Browser Control - Navigate and interact with web pages
Step 2: Form Detection - Find form fields on a page
Step 3: Form Filling - Fill fields with provided data
Step 4: Form Submission - Submit completed forms

Key Concept: Browser automation tools allow agents to interact with web pages
just like a human would, enabling form filling, clicking, and navigation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Global browser instance (reused across requests)
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None


async def get_browser():
    """Get or create browser instance"""
    global _browser, _context
    
    if _browser is None:
        playwright = await async_playwright().start()
        _browser = await playwright.chromium.launch(headless=True)
        _context = await _browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
    
    return _browser, _context


async def close_browser():
    """Close browser instance"""
    global _browser, _context
    
    if _context:
        await _context.close()
        _context = None
    if _browser:
        await _browser.close()
        _browser = None


@tool
def navigate_to_url(url: str) -> str:
    """
    Navigate to a specific URL in the browser.
    
    Args:
        url: The URL to navigate to (must include http:// or https://)
    
    Returns:
        Status message with page title and URL
    """
    import asyncio
    try:
        async def _navigate():
            _, context = await get_browser()
            page = await context.new_page()
            
            logger.info(f"Navigating to: {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            title = await page.title()
            current_url = page.url
            
            await page.close()
            
            return f"Navigated to {url}. Page title: {title}. Current URL: {current_url}"
        
        return asyncio.run(_navigate())
        
    except Exception as e:
        logger.error(f"Error navigating to {url}: {e}")
        return f"Error navigating to URL: {str(e)}"


@tool
def detect_form_fields(url: str) -> str:
    """
    Detect all form fields on a webpage.
    
    This tool analyzes a webpage and identifies all input fields, textareas,
    select dropdowns, and other form elements.
    
    Args:
        url: The URL of the webpage to analyze
    
    Returns:
        JSON string with form field information (id, name, type, label, placeholder)
    """
    import asyncio
    try:
        async def _detect():
            _, context = await get_browser()
            page = await context.new_page()
            
            logger.info(f"Detecting form fields on: {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Extract form field information
            form_fields = await page.evaluate("""
            () => {
                const fields = [];
                const inputs = document.querySelectorAll('input, textarea, select');
                
                inputs.forEach((input, index) => {
                    const field = {
                        index: index,
                        id: input.id || '',
                        name: input.name || '',
                        type: input.type || input.tagName.toLowerCase(),
                        label: '',
                        placeholder: input.placeholder || '',
                        required: input.required || false,
                        value: input.value || ''
                    };
                    
                    // Try to find associated label
                    if (input.id) {
                        const label = document.querySelector(`label[for="${input.id}"]`);
                        if (label) {
                            field.label = label.textContent.trim();
                        }
                    }
                    
                    // If no label found, look for parent label
                    if (!field.label) {
                        const parentLabel = input.closest('label');
                        if (parentLabel) {
                            field.label = parentLabel.textContent.trim();
                        }
                    }
                    
                    fields.push(field);
                });
                
                return fields;
            }
        """)
            
            await page.close()
            
            import json
            return json.dumps(form_fields, indent=2)
        
        return asyncio.run(_detect())
        
    except Exception as e:
        logger.error(f"Error detecting form fields: {e}")
        return f"Error detecting form fields: {str(e)}"


@tool
def fill_form(url: str, form_data: Dict[str, str]) -> str:
    """
    Fill a form on a webpage with provided data.
    
    This tool navigates to a URL, identifies form fields, and fills them
    with the provided data. It matches fields by id, name, or label.
    
    Args:
        url: The URL of the webpage with the form
        form_data: Dictionary mapping field identifiers to values
                  (can use field id, name, or label text)
    
    Returns:
        Status message with details of filled fields
    """
    import asyncio
    import json
    try:
        async def _fill():
            _, context = await get_browser()
            page = await context.new_page()
            
            logger.info(f"Filling form on: {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            filled_fields = []
            errors = []
            
            # Get all form fields
            form_fields = await page.evaluate("""
            () => {
                const fields = [];
                const inputs = document.querySelectorAll('input, textarea, select');
                
                inputs.forEach((input) => {
                    fields.push({
                        id: input.id || '',
                        name: input.name || '',
                        type: input.type || input.tagName.toLowerCase(),
                        label: ''
                    });
                    
                    if (input.id) {
                        const label = document.querySelector(`label[for="${input.id}"]`);
                        if (label) {
                            fields[fields.length - 1].label = label.textContent.trim();
                        }
                    }
                });
                
                return fields;
            }
            """)
            
            # Fill each field
            for field_identifier, value in form_data.items():
                field_found = False
                
                for field in form_fields:
                    # Match by id, name, or label (case-insensitive)
                    if (field_identifier.lower() in field['id'].lower() or
                        field_identifier.lower() in field['name'].lower() or
                        field_identifier.lower() in field['label'].lower()):
                        
                        try:
                            if field['type'] == 'select':
                                # Handle select dropdowns
                                await page.select_option(
                                    f"select#{field['id']}" if field['id'] else f"select[name='{field['name']}']",
                                    value
                                )
                            else:
                                # Handle input and textarea
                                selector = (
                                    f"#{field['id']}" if field['id'] 
                                    else f"[name='{field['name']}']"
                                )
                                await page.fill(selector, value)
                            
                            filled_fields.append(f"{field_identifier} = {value}")
                            field_found = True
                            break
                        except Exception as e:
                            errors.append(f"Error filling {field_identifier}: {str(e)}")
                
                if not field_found:
                    errors.append(f"Field '{field_identifier}' not found on page")
            
            # Take a screenshot for verification (after all fields are filled)
            screenshot_path = f"/tmp/form_filled_{hash(url)}.png"
            await page.screenshot(path=screenshot_path)
            
            await page.close()
            
            result = f"Form filling completed.\n"
            result += f"Filled {len(filled_fields)} fields:\n"
            for field in filled_fields:
                result += f"  - {field}\n"
            
            if errors:
                result += f"\nErrors:\n"
                for error in errors:
                    result += f"  - {error}\n"
            
            return result
        
        return asyncio.run(_fill())
        
    except Exception as e:
        logger.error(f"Error filling form: {e}")
        return f"Error filling form: {str(e)}"


@tool
def submit_form(url: str, submit_button_text: Optional[str] = None) -> str:
    """
    Submit a form on a webpage.
    
    Args:
        url: The URL of the webpage with the form
        submit_button_text: Optional text to identify submit button (e.g., "Submit", "Send")
    
    Returns:
        Status message with submission result
    """
    import asyncio
    try:
        async def _submit():
            _, context = await get_browser()
            page = await context.new_page()
            
            logger.info(f"Submitting form on: {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Try to find and click submit button
            if submit_button_text:
                await page.click(f"button:has-text('{submit_button_text}')")
            else:
                # Try common submit button selectors
                submit_selectors = [
                    'input[type="submit"]',
                    'button[type="submit"]',
                    'button:has-text("Submit")',
                    'button:has-text("Send")',
                    'button:has-text("Send Message")'
                ]
                
                submitted = False
                for selector in submit_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        submitted = True
                        break
                    except:
                        continue
                
                if not submitted:
                    await page.close()
                    return "Could not find submit button. Form may need manual submission."
            
            # Wait for navigation or response
            await page.wait_for_timeout(2000)
            
            current_url = page.url
            page_title = await page.title()
            
            await page.close()
            
            return f"Form submitted successfully. Current URL: {current_url}. Page title: {page_title}"
        
        return asyncio.run(_submit())
        
    except Exception as e:
        logger.error(f"Error submitting form: {e}")
        return f"Error submitting form: {str(e)}"


def get_all_tools() -> List:
    """Get all available browser automation tools"""
    return [
        navigate_to_url,
        detect_form_fields,
        fill_form,
        submit_form
    ]

