# Read_Report_v2: Interactive Topic Modeling

**Read_Report_v2** is an interactive web-based tool aimed at performing **Latent Dirichlet Allocation (LDA)** topic modeling on text datasets. It features a "Human-in-the-Loop" workflow, allowing users to analyze topics, refine results by banning stopwords interactively, and automatically persist trained models to the cloud.

## Key Features

### 1. Advanced Topic Modeling
- **Dynamic K-Selection**: Automatically finds the optimal number of topics (K=3 to 20) by maximizing the **Coherence Score ($C_v$)**.
- **LDA Implementation**: Powered by `gensim` for robust probabilistic modeling.

### 2. Interactive Refinement
- **Web Interface**: A Flask-based UI accepts text input and visualizes dominant topics.
- **Click-to-Ban**: Users can click on irrelevant words in the topic output to "ban" them.
- **Auto-Retraining**: Banned words are added to a persistent exclusion list (`custom_stopwords.json`), and the model can be triggered to retrain immediately.

### 3. Cloud Native Persistence
- **Google Cloud Storage (GCS) Integration**: Models are not just saved locally but uploaded to a GCS bucket.
- **Versioning**: Models are stored in timestamped folders (e.g., `models/edh/20251222_150000/`) to prevent conflicts.
- **Smart Overwrites**: Upon successful training, the system automatically preserves the latest version and cleans up older versions in GCS to save space.
- **State Awareness**: The training logic checks if a model already exists to prevent redundant processing, with a user-override ("Force Retrain") available in the UI.

## Setup & specific configuration

### Prerequisites
- Python 3.10+
- A Google Cloud Platform project with a GCS Bucket.
- A Service Account Key JSON file.

### Installation

1.  **Clone & Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file in the root directory:
    ```env
    GCS_BUCKET_NAME=your_bucket_name
    GOOGLE_APPLICATION_CREDENTIALS=google_credentials.json
    ```

3.  **Credentials**:
    - Place your service account key file in the root as `google_credentials.json`.
    - **Note**: This file is ignored by `.gitignore` for security but included in deployment via `.gcloudignore`.

## Usage

### Running Locally
Start the web application:
```bash
python app.py
```
Access the UI at `http://localhost:8080`.

### Manual Training
You can also train the model from the CLI:
```bash
# Train for specific media
python train_model.py --media edh

# Force retrain (ignore existing models)
python train_model.py --media edh --force
```

## Deployment

### Docker / Cloud Run
The project is container-ready.
1.  **Build**:
    ```bash
    docker build -t read-report-v2 .
    ```
2.  **Deploy**:
    Ensure your `.gcloudignore` is set up to include your credentials file.
    ```bash
    gcloud run deploy read-report-v2 --source .
    ```

## File Structure
- `app.py`: Main Flask application entry point.
- `train_model.py`: Script handling data loading, preprocessing, LDA training, and GCS upload.
- `gcs_handler.py`: Helper module for GCS operations (upload, download, list, delete).
- `model_utils.py`: Utilities for loading models (with fallback to GCS) and generating predictions.
- `static/main.js`: Frontend logic for interaction and API calls.
