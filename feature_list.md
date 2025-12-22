# Project Feature List: Read_Report_v2

This project is an **Interactive Topic Modeling Tool** that allows users to analyze text, discover topics, and interactively refine the model by excluding irrelevant words.

## Core capabilities

### 1. Advanced Topic Modeling (LDA)
- **Automated Training**: Utilizes Latent Dirichlet Allocation (LDA) via `gensim` to discover abstract topics within text corpora.
- **Auto-Tuning (Dynamic K)**: Automatically iterates through a range of topic counts (K=3 to K=20) to find the optimal number of topics based on the highest **Coherence Score (c_v)**.
- **Multi-Dataset Support**: Capable of training and serving distinct models for different "media" types (datasets) independently (e.g., separating "edh" data from general data).

### 2. Interactive Web Interface
- **Real-time Prediction**: Users can paste text to instantly analyze and view the dominant topics and their constituent keywords.
- **On-Demand Training**: Provides a UI control to trigger model retraining directly from the browser, with progress feedback.
- **Coherence Analytics**: Displays detailed coherence scores for each 'K' value in the developer console for deep-dive analysis.

### 3. Model Refinement Loop ("Human-in-the-Loop")
- **Click-to-Ban Interaction**: Users can interactively click on specific keywords within the prediction results to flag them as irrelevant (stopwords).
- **Persistent Custom Stopwords**: Flagged words are saved to a persistent generic JSON store (`custom_stopwords.json`), ensuring they are remembered for future training sessions.
- **Automatic Retraining**: The system seamlessly adds the new stopwords and triggers a full model retrain in one workflow, allowing users to immediately see the impact of their refinements.

### 4. System Architecture
- **Flask Backend**: A lightweight Python API serving the frontend and handling model logic.
- **Model Persistence**: Trained models and dictionaries are serialized and saved to disk (`models/<media>/`), allowing for quick loading without retraining.
- **Smart Caching**: Loaded models are cached in memory to speed up prediction, with automatic cache invalidation when a new model is trained.
