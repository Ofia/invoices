"""
Gmail Integration Service

This module handles fetching emails from Gmail and detecting invoice attachments.

Flow:
1. User clicks "Sync Gmail" in workspace
2. We use stored refresh_token to get a fresh access_token
3. Search Gmail for emails with PDF attachments
4. Filter by:
   - Sender matches known supplier email OR
   - Subject contains keywords ("invoice", "bill")
5. Download PDF attachments to storage
6. Create pending_documents for user review
7. Track gmail_message_id to prevent duplicates

Gmail API Docs: https://developers.google.com/gmail/api
"""

import logging
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.supplier import Supplier
from app.models.pending_document import PendingDocument
from app.models.processed_email import ProcessedEmail
from app.core.config import settings
from app.utils.storage import save_document_file

logger = logging.getLogger(__name__)


# Invoice detection keywords in subject line
INVOICE_KEYWORDS = [
    "invoice",
    "bill",
    "payment",
    "receipt",
    "statement",
    "balance due",
    "amount due"
]


def refresh_access_token(user: User) -> Optional[str]:
    """
    Refresh the user's access token using their refresh token.

    Args:
        user: User object with refresh_token

    Returns:
        New access token string, or None if refresh failed

    Raises:
        Exception: If refresh token is missing or refresh fails
    """
    if not user.refresh_token:
        raise Exception("User has no refresh token. Please re-authenticate with Gmail scope.")

    try:
        # Create credentials object with refresh token
        credentials = Credentials(
            token=None,  # No access token yet
            refresh_token=user.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GOOGLE_OAUTH_SCOPES
        )

        # Force refresh
        from google.auth.transport.requests import Request
        credentials.refresh(Request())

        logger.info(f"Successfully refreshed access token for user {user.id}")
        return credentials.token

    except Exception as e:
        logger.error(f"Failed to refresh access token for user {user.id}: {str(e)}")
        raise Exception(f"Failed to refresh Gmail access token: {str(e)}")


def build_gmail_service(access_token: str):
    """
    Build Gmail API service with access token.

    Args:
        access_token: OAuth access token

    Returns:
        Gmail API service object
    """
    credentials = Credentials(token=access_token)
    return build('gmail', 'v1', credentials=credentials)


def search_gmail_for_invoices(
    gmail_service,
    supplier_emails: List[str],
    last_sync_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Search Gmail for emails with PDF attachments that match invoice criteria.

    Detection strategy:
    - Email has PDF attachment
    - Sender matches known supplier email OR subject contains invoice keywords
    - After last_sync_date (if provided)

    Args:
        gmail_service: Gmail API service object
        supplier_emails: List of known supplier emails
        last_sync_date: Only fetch emails after this date

    Returns:
        List of message objects that match invoice criteria
    """
    try:
        # Build search query
        query_parts = [
            "has:attachment",
            "filename:pdf"
        ]

        # Add date filter if provided
        if last_sync_date:
            date_str = last_sync_date.strftime("%Y/%m/%d")
            query_parts.append(f"after:{date_str}")

        # Construct OR conditions for supplier emails and keywords
        or_conditions = []

        # Add supplier emails
        for email in supplier_emails:
            or_conditions.append(f"from:{email}")

        # Add subject keywords
        for keyword in INVOICE_KEYWORDS:
            or_conditions.append(f'subject:"{keyword}"')

        # Combine with OR
        if or_conditions:
            or_query = " OR ".join(or_conditions)
            query_parts.append(f"({or_query})")

        query = " ".join(query_parts)
        logger.info(f"Gmail search query: {query}")

        # Execute search
        results = gmail_service.users().messages().list(
            userId='me',
            q=query,
            maxResults=100  # Limit to avoid overwhelming
        ).execute()

        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} matching emails")

        return messages

    except HttpError as e:
        logger.error(f"Gmail API error: {str(e)}")
        raise Exception(f"Failed to search Gmail: {str(e)}")


def get_message_details(gmail_service, message_id: str) -> Dict[str, Any]:
    """
    Get full message details including headers and attachments.

    Args:
        gmail_service: Gmail API service object
        message_id: Gmail message ID

    Returns:
        Dictionary with message details
    """
    try:
        message = gmail_service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        return message

    except HttpError as e:
        logger.error(f"Failed to get message {message_id}: {str(e)}")
        raise Exception(f"Failed to get message details: {str(e)}")


def extract_sender_email(message: Dict[str, Any]) -> Optional[str]:
    """
    Extract sender email from message headers.

    Args:
        message: Gmail message object

    Returns:
        Sender email address or None
    """
    headers = message.get('payload', {}).get('headers', [])

    for header in headers:
        if header['name'].lower() == 'from':
            # Format: "Name <email@example.com>" or "email@example.com"
            from_value = header['value']
            if '<' in from_value and '>' in from_value:
                # Extract email from "Name <email>"
                return from_value.split('<')[1].split('>')[0].strip()
            else:
                return from_value.strip()

    return None


def extract_subject(message: Dict[str, Any]) -> str:
    """
    Extract subject from message headers.

    Args:
        message: Gmail message object

    Returns:
        Subject string
    """
    headers = message.get('payload', {}).get('headers', [])

    for header in headers:
        if header['name'].lower() == 'subject':
            return header['value']

    return "(No Subject)"


async def download_pdf_attachments(
    gmail_service,
    message: Dict[str, Any],
    workspace_id: int
) -> List[Dict[str, Any]]:
    """
    Download all PDF attachments from a message.

    Args:
        gmail_service: Gmail API service object
        message: Gmail message object
        workspace_id: Workspace ID for storage

    Returns:
        List of dictionaries with attachment info:
        [
            {
                "filename": "invoice.pdf",
                "file_path": "uploads/workspace_1/uuid.pdf",
                "size": 12345
            }
        ]
    """
    attachments = []
    parts = message.get('payload', {}).get('parts', [])

    async def process_part(part):
        """Recursively process message parts"""
        filename = part.get('filename', '')

        # Check if this part is a PDF attachment
        if filename.lower().endswith('.pdf') and part.get('body', {}).get('attachmentId'):
            attachment_id = part['body']['attachmentId']

            try:
                # Download attachment
                attachment = gmail_service.users().messages().attachments().get(
                    userId='me',
                    messageId=message['id'],
                    id=attachment_id
                ).execute()

                # Decode attachment data
                file_data = base64.urlsafe_b64decode(attachment['data'])

                # Save to storage
                from io import BytesIO
                file_content = BytesIO(file_data)
                file_path = await save_document_file(
                    file_content=file_content,
                    workspace_id=workspace_id,
                    original_filename=filename
                )

                attachments.append({
                    "filename": filename,
                    "file_path": file_path,
                    "size": len(file_data)
                })

                logger.info(f"Downloaded attachment: {filename} ({len(file_data)} bytes)")

            except Exception as e:
                logger.error(f"Failed to download attachment {filename}: {str(e)}")

        # Process nested parts (for multipart messages)
        if 'parts' in part:
            for sub_part in part['parts']:
                await process_part(sub_part)

    # Process all parts
    for part in parts:
        await process_part(part)

    return attachments


async def sync_gmail_invoices(
    db: Session,
    user: User,
    workspace_id: int,
    days_back: int = 7
) -> Dict[str, Any]:
    """
    Main function to sync Gmail and create pending documents for invoices.

    Args:
        db: Database session
        user: User object with Gmail OAuth tokens
        workspace_id: Workspace to sync invoices to
        days_back: Number of days to look back (default: 7, max: 90)

    Returns:
        Dictionary with sync statistics:
        {
            "emails_scanned": 25,
            "invoices_detected": 5,
            "documents_created": 3,
            "duplicates_skipped": 2
        }
    """
    try:
        # Step 1: Refresh access token
        logger.info(f"Starting Gmail sync for user {user.id}, workspace {workspace_id}")
        access_token = refresh_access_token(user)

        # Update user's access token in DB
        user.oauth_token = access_token
        db.commit()

        # Step 2: Build Gmail service
        gmail_service = build_gmail_service(access_token)

        # Step 3: Get known supplier emails for this workspace
        suppliers = db.query(Supplier).filter(
            Supplier.workspace_id == workspace_id,
            Supplier.email.isnot(None)
        ).all()
        supplier_emails = [s.email for s in suppliers if s.email]

        logger.info(f"Searching for emails from {len(supplier_emails)} known suppliers")

        # Step 4: Determine last sync date based on days_back parameter
        last_sync_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        logger.info(f"Searching emails from {last_sync_date.date()} to now ({days_back} days)")

        # Step 5: Search Gmail
        messages = search_gmail_for_invoices(
            gmail_service=gmail_service,
            supplier_emails=supplier_emails,
            last_sync_date=last_sync_date
        )

        # Step 6: Process each message
        stats = {
            "emails_scanned": len(messages),
            "invoices_detected": 0,
            "documents_created": 0,
            "duplicates_skipped": 0
        }

        for msg_summary in messages:
            message_id = msg_summary['id']

            # Check if already processed
            existing = db.query(ProcessedEmail).filter(
                ProcessedEmail.gmail_message_id == message_id
            ).first()

            if existing:
                stats["duplicates_skipped"] += 1
                continue

            # Get full message details
            message = get_message_details(gmail_service, message_id)

            # Extract metadata
            sender_email = extract_sender_email(message)
            subject = extract_subject(message)

            logger.info(f"Processing email from {sender_email}: {subject}")

            # Download PDF attachments
            attachments = await download_pdf_attachments(
                gmail_service=gmail_service,
                message=message,
                workspace_id=workspace_id
            )

            if not attachments:
                logger.info(f"No PDF attachments found in message {message_id}")
                continue

            stats["invoices_detected"] += len(attachments)

            # Create pending documents for each attachment
            for attachment in attachments:
                pending_doc = PendingDocument(
                    workspace_id=workspace_id,
                    filename=attachment["filename"],
                    pdf_url=attachment["file_path"],
                    gmail_message_id=message_id,
                    status="pending"
                )
                db.add(pending_doc)
                stats["documents_created"] += 1

            # Mark email as processed
            processed_email = ProcessedEmail(
                gmail_message_id=message_id,
                workspace_id=workspace_id
            )
            db.add(processed_email)

        # Commit all changes
        db.commit()

        logger.info(
            f"Gmail sync complete: {stats['documents_created']} documents created, "
            f"{stats['duplicates_skipped']} duplicates skipped"
        )

        return stats

    except Exception as e:
        logger.error(f"Gmail sync failed: {str(e)}")
        db.rollback()
        raise Exception(f"Gmail sync failed: {str(e)}")
