# Gmail Sync Date Range Feature

## Overview
Added configurable date range control to Gmail sync to prevent processing thousands of old emails.

## Parameters

### `days_back` (Optional Query Parameter)
- **Type:** Integer
- **Range:** 1 to 90 days
- **Default:** 7 days
- **Maximum:** 90 days (3 months)

## Safety Measures

### Why 90-Day Maximum?
1. **Performance:** Prevents overwhelming the system with thousands of emails
2. **Storage:** Limits number of PDFs downloaded and stored
3. **User Experience:** Keeps pending document queue manageable
4. **API Quotas:** Respects Gmail API rate limits (100 emails/request)
5. **Cost Control:** Limits storage and processing costs

### Default: 7 Days
- Safe starting point for first-time sync
- Typical invoice frequency for most businesses
- Quick sync time
- Easy to review queue

## Usage Examples

### Default (Last 7 Days)
```bash
POST /gmail/sync?workspace_id=1
```

### Last Month
```bash
POST /gmail/sync?workspace_id=1&days_back=30
```

### Maximum Range (3 Months)
```bash
POST /gmail/sync?workspace_id=1&days_back=90
```

### Invalid Range (Will Return 422 Validation Error)
```bash
POST /gmail/sync?workspace_id=1&days_back=365
# Error: Value greater than maximum allowed (90)
```

## Validation

FastAPI automatically validates the parameter:
- ✅ `days_back=1` → Valid (minimum)
- ✅ `days_back=7` → Valid (default)
- ✅ `days_back=30` → Valid
- ✅ `days_back=90` → Valid (maximum)
- ❌ `days_back=0` → Error (422 Validation Error)
- ❌ `days_back=91` → Error (422 Validation Error)
- ❌ `days_back=-5` → Error (422 Validation Error)

## Recommended Workflow

### First-Time Sync
1. Start with **7 days** (default)
2. Review the pending documents queue
3. Approve/reject as needed

### Catching Up on Older Invoices
1. Use **30 days** for the previous month
2. Process the queue
3. If needed, use **90 days** for quarterly catch-up

### Ongoing Maintenance
- Sync weekly with **7 days** (default)
- Or sync monthly with **30 days**

## Implementation Details

### Code Changes

**API Route (`app/api/routes/gmail.py`):**
```python
async def sync_gmail(
    workspace_id: int = Query(...),
    days_back: int = Query(7, ge=1, le=90),  # ← New parameter
    ...
)
```

**Service Function (`app/services/gmail_service.py`):**
```python
async def sync_gmail_invoices(
    db: Session,
    user: User,
    workspace_id: int,
    days_back: int = 7  # ← New parameter
):
    # Calculate date range
    last_sync_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    ...
```

## Error Handling

### Invalid Range Response
```json
{
    "detail": [
        {
            "type": "less_than_equal",
            "loc": ["query", "days_back"],
            "msg": "Input should be less than or equal to 90",
            "input": "365",
            "ctx": {"le": 90}
        }
    ]
}
```

## Benefits

1. ✅ **Control:** Users decide how far back to search
2. ✅ **Safety:** Maximum 90-day limit prevents abuse
3. ✅ **Performance:** Smaller date ranges = faster syncs
4. ✅ **Flexible:** Adjust based on business needs
5. ✅ **Default:** Sensible 7-day default for most use cases

## Future Enhancements (Optional)

Possible future improvements:
- Track last successful sync date per workspace
- Auto-suggest date range based on last sync
- Allow workspace-specific limits (e.g., premium users get 180 days)
- Add warning when selecting large date ranges
- Show estimated email count before syncing
