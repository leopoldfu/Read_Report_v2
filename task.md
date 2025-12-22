# Task: Enforce GCS Persistence for Stopwords

The goal is to ensure that stopwords (both base templates and custom banned words) are strictly stored in and accessed from Google Cloud Storage. This ensures consistency across distributed application instances and prevents stale data issues.

- [x] Modify `stopwords.py` to **always** attempt downloading `base_stopwords.json` and `custom_stopwords.json` from GCS before reading. <!-- id: 1 -->
- [ ] Verify `app.py` ensures strict fresh-read before update (already verified, but double-check). <!-- id: 2 -->
- [x] Seeding: Implement seeding mechanism within `app.py` startup since local script cannot be run. <!-- id: 3 -->
- [ ] Verify functionality via `debug_model.py` or similar trace. <!-- id: 4 -->
