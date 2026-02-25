# Invoice Adjuster — Open Tasks

## Open

- [ ] **AI currency detection**: Claude currently extracts `total_amount` as a raw number without identifying the invoice currency. Non-EUR amounts (e.g. Costa Rican CRC ₡40,000) are stored and displayed as if they were EUR, causing wildly incorrect markup totals. Fix: extend the AI extraction prompt to also return `currency` (ISO 4217 code), then convert to a base currency (EUR) before storing, or store the original currency and amount separately and convert at display time.
