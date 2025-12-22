import json
import os
import argparse
import pandas as pd
from tqdm import tqdm
from gensim.corpora import Dictionary
from gensim.models import LdaModel
from gensim.models.coherencemodel import CoherenceModel
import warnings
import stopwords
import gcs_handler
from datetime import datetime
from dotenv import load_dotenv
import string

# Load environment variables
load_dotenv()

# Suppress DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

def clean_tokens(words, stop_words):
    tokens = []
    for w in words:
        if not isinstance(w, str):
            continue
        w = w.strip()
        if not w:
            continue
        if w in stop_words:
            continue
        if len(w) <= 1:
            continue
        tokens.append(w)
    return tokens

def train(media="edh", force=False):
    """
    Train LDA model for a specific media.
    Returns:
        dict: result status and message
    """
    print(f"Starting training for {media}...")
    
    # --- Check GCS for existing models ---
    if not force:
        existing_versions = gcs_handler.list_model_versions(media)
        if existing_versions:
            msg = f"Model for '{media}' already exists in GCS (versions: {existing_versions}). Skipping training. Use force=True to re-train."
            print(msg)
            return {"success": True, "message": msg, "skipped": True}
    # -------------------------------------

    data_dir = os.path.join("data", media)
    model_dir = os.path.join("models", media)
    
    # Input/Output Paths
    train_json_path = os.path.join(data_dir, "edh_keywords_2025_new.json") 
    
    if media != "edh" and not os.path.exists(train_json_path):
         # Try generic name
         train_json_path = os.path.join(data_dir, "training_data.json")

    model_save_path = os.path.join(model_dir, "lda.model")
    dict_save_path = os.path.join(model_dir, "id2word.dict")

    if not os.path.exists(train_json_path):
        return {"success": False, "message": f"Training data not found at {train_json_path}"}

    os.makedirs(model_dir, exist_ok=True)

    try:
        print(f"Loading data for '{media}'...")
        with open(train_json_path, "r", encoding="utf-8") as f:
            raw_docs = json.load(f)

        # Get Stopwords
        stop_words_set = stopwords.get_stopwords(media)

        train_docs = []
        print("Preprocessing...")
        # Note: tqdm might clutter logs in web app context, mainly for CLI
        for doc in raw_docs: 
            words = doc.get("word", [])
            if isinstance(words, list):
                tokens = clean_tokens(words, stop_words_set)
                if len(tokens) >= 3:
                    train_docs.append(tokens)

        print("Training documents:", len(train_docs))
        if len(train_docs) == 0:
            return {"success": False, "message": "No valid documents found after preprocessing."}

        # Create Dictionary
        id2word = Dictionary(train_docs)
        corpus = [id2word.doc2bow(text) for text in train_docs]

        best_k = 10 
        best_score = -1.0
        best_model = None

        print("Calculating Coherence Scores for K=3..20...")
        # Loop to find best K
        coherence_scores = []
        for k in range(3, 21):
            # Train temp model
            lda_temp = LdaModel(
                corpus=corpus,
                id2word=id2word,
                num_topics=k,
                random_state=42,
                passes=10,
                alpha='auto',
                per_word_topics=True
            )
            
            # Calculate consistency
            cm = CoherenceModel(
                model=lda_temp,
                texts=train_docs,
                dictionary=id2word,
                coherence='c_v'
            )
            score = cm.get_coherence()
            msg = f"K={k} → Coherence={score:.4f}"
            print(msg)
            coherence_scores.append({"k": k, "score": score})
            
            if score > best_score:
                best_score = score
                best_k = k
                best_model = lda_temp

        print(f"Selected Best K={best_k} (Coherence={best_score:.4f})")
        
        # Use best model
        lda_final = best_model

        print(f"Saving model to {model_save_path}...")
        lda_final.save(model_save_path)
        id2word.save(dict_save_path)
        
        # --- GCS Upload & Cleanup ---
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gcs_version_path = f"models/{media}/{timestamp}"
        
        print(f"Uploading model to GCS version: {timestamp}...")
        gcs_handler.upload_folder(model_dir, gcs_version_path)
        
        # Cleanup old versions (Overwrite logic)
        existing = gcs_handler.list_model_versions(media)
        for old_ver in existing:
            if old_ver != timestamp:
                print(f"Removing old version {old_ver} from GCS...")
                gcs_handler.delete_version(media, old_ver)
        # ----------------------------

        print("Done.")
        return {
            "success": True, 
            "message": f"Model trained for {media} with K={best_k} (Score={best_score:.4f}). Saved version {timestamp}.",
            "scores": coherence_scores
        }
    
    except Exception as e:
        print(f"Training failed: {e}")
        return {"success": False, "message": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Train LDA model for a specific media.")
    parser.add_argument("--media", type=str, default="edh", help="Media name (folder name in data/)")
    parser.add_argument("--force", action="store_true", help="Force retraining even if model exists in GCS")
    args = parser.parse_args()
    
    result = train(args.media, force=args.force)
    print(result)

if __name__ == "__main__":
    main()
