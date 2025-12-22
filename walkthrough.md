# Walkthrough - GCS Seeding for Stopwords

Since local scripts cannot be run in your environment, I have implemented a **self-seeding capability** within the web application.

## How to Initialize Stopwords in GCS

Once your application is deployed to Cloud Run (or running in a container), you need to upload the initial `base_stopwords.json` to your GCS bucket.

**Step 1: Deploy the App**
Ensure your app is running.

**Step 2: Trigger the Seeding**
You can trigger the upload by sending a POST request to the new endpoint. You can use `curl` or Postman.

```bash
# Replace YOUR_APP_URL with your actual Cloud Run URL
curl -X POST https://YOUR_APP_URL/seed_stopwords \
     -H "Content-Type: application/json" \
     -d '{"media": "edh"}'
```

**Response:**
- Success: `{"success": true, "message": "Seeded stopwords/edh/base_stopwords.json"}`
- Failure: Error message explaining why (e.g., credentials missing).

## How Updates Work
1.  **Read**: Every time the model trains or analyzes, it fetches the *latest* files from GCS.
2.  **Write**: When you ban words in the UI, the app uploads the new list to GCS immediately.
3.  **Result**: All instances stay in sync.
