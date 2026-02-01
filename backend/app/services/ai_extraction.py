"""
AI Invoice Data Extraction Service

Uses Anthropic's Claude API to extract structured data from invoice text.

Flow:
1. Receive raw text from document
2. Send to Claude with structured extraction prompt
3. Parse JSON response containing invoice data
4. Return structured data for invoice creation
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import date
from anthropic import Anthropic
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


INVOICE_EXTRACTION_PROMPT = """You are an invoice data extraction assistant. Extract the following information from the invoice text below:

1. **supplier_email**: The email address of the supplier/vendor (company that sent the invoice)
2. **invoice_date**: The date of the invoice in YYYY-MM-DD format
3. **total_amount**: The total amount due (final total, not subtotals)

Rules:
- If you cannot find a field, set it to null
- For invoice_date, convert any date format to YYYY-MM-DD (e.g., "12/10/2025" → "2025-12-10")
- For total_amount, extract only the numeric value (e.g., "$100.00" → 100.00)
- Look for keywords like "Total", "Amount Due", "Balance Due" for the total
- Return ONLY valid JSON, no explanations

Response format (JSON only):
{{
  "supplier_email": "billing@company.com",
  "invoice_date": "2025-12-10",
  "total_amount": 100.00
}}

Invoice text:
---
{invoice_text}
---

Extract the data as JSON:"""


async def extract_invoice_data(document_text: str) -> Dict[str, Any]:
    """
    Extract structured invoice data from document text using Claude AI.

    Args:
        document_text: Raw text extracted from invoice document

    Returns:
        Dictionary containing:
        {
            "supplier_email": "billing@abc.com",
            "invoice_date": "2025-12-10",
            "total_amount": 100.00
        }

    Raises:
        Exception: If API call fails or response cannot be parsed

    Example:
        >>> text = "INVOICE\\nFrom: ABC Electric (billing@abc.com)\\nDate: 12/10/2025\\nTotal: $100.00"
        >>> data = await extract_invoice_data(text)
        >>> print(data)
        {"supplier_email": "billing@abc.com", "invoice_date": "2025-12-10", "total_amount": 100.00}
    """
    try:
        # Build prompt with invoice text
        prompt = INVOICE_EXTRACTION_PROMPT.format(invoice_text=document_text)

        logger.info(f"Sending {len(document_text)} chars to Claude for extraction")

        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",  # Claude Sonnet 4.5 (latest)
            max_tokens=1024,
            temperature=0,  # Deterministic output for data extraction
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract text response
        response_text = message.content[0].text
        logger.info(f"Claude extraction response received ({len(response_text)} chars)")

        # Parse JSON response
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Sometimes Claude returns JSON in markdown code blocks
            # Try to extract JSON from ```json ... ``` blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
                data = json.loads(json_text)
            elif "```" in response_text:
                # Plain ``` blocks
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
                data = json.loads(json_text)
            else:
                raise Exception(f"Could not parse JSON from response: {response_text}")

        # Validate required fields
        if not isinstance(data, dict):
            raise Exception(f"Response is not a JSON object: {data}")

        # Return extracted data
        return {
            "supplier_email": data.get("supplier_email"),
            "invoice_date": data.get("invoice_date"),
            "total_amount": data.get("total_amount")
        }

    except Exception as e:
        logger.error(f"AI extraction failed: {str(e)}")
        raise Exception(f"Failed to extract invoice data: {str(e)}")


def validate_extracted_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate extracted invoice data.

    Args:
        data: Extracted data dictionary

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> data = {"supplier_email": None, "invoice_date": "2025-12-10", "total_amount": 100}
        >>> is_valid, error = validate_extracted_data(data)
        >>> print(is_valid, error)
        False "Missing required field: supplier_email"
    """
    # Check required fields
    if not data.get("supplier_email"):
        return False, "Missing required field: supplier_email"

    if not data.get("total_amount"):
        return False, "Missing required field: total_amount"

    # Validate total_amount is positive number
    try:
        amount = float(data["total_amount"])
        if amount <= 0:
            return False, "Total amount must be greater than 0"
    except (ValueError, TypeError):
        return False, f"Invalid total_amount: {data.get('total_amount')}"

    # Validate date format (YYYY-MM-DD)
    if data.get("invoice_date"):
        try:
            date.fromisoformat(data["invoice_date"])
        except (ValueError, TypeError):
            return False, f"Invalid date format: {data.get('invoice_date')} (expected YYYY-MM-DD)"

    return True, None
