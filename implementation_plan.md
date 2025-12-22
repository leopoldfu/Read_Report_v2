# Admin Seeding Endpoint Implementation Plan

Since local GCS access is unavailable, we will implement a self-seeding mechanism within the deployed app.

## Goals
1.  Allow the deployed application to upload its local `base_stopwords.json` to GCS.
2.  Ensure `stopwords.py` always fetches the latest version from GCS (re-applying the freshness logic).

## Changes

### Backend
#### [MODIFY] [app.py](file:///Users/leopoldfu/dev/Read_Report_v2/app.py)
- Add route `POST /seed_stopwords`.
- **Logic**:
    1.  Define path `data/edh/base_stopwords.json`.
    2.  Check if exists locally.
    3.  Call `gcs_handler.upload_file` to Upload to `stopwords/edh/base_stopwords.json`.
    4.  Return success/fail.

#### [MODIFY] [stopwords.py](file:///Users/leopoldfu/dev/Read_Report_v2/stopwords.py)
- Re-apply the "Always Download" pattern.
- **Reason**: The user wants "everytime ban words added, it updates". If we cache locally and never check GCS again, one instance won't see another instance's updates until restart. The cost of one small file download per analysis is negligible compared to model inference.

## Verification
1.  Deploy App.
2.  Call `curl -X POST https://app-url/seed_stopwords`.
3.  Verify GCS bucket has the file.
