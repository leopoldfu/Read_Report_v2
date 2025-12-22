import os
import json
import gcs_handler

def get_stopwords(media_name="edh"):
    """
    Return stopwords set for the specific media.
    Merges hardcoded base list with 'data/{media_name}/custom_stopwords.json'.
    """
    # Common/Base stopwords could go here if shared
    base_stopwords = {
        "身體","感覺","覺得","注意","地方","保持","效果","現在" # General stopwords
    }

    
    # --- Load Base Stopwords (Template) ---
    base_path = os.path.join("data", media_name, "base_stopwords.json")
    base_gcs = f"stopwords/{media_name}/base_stopwords.json"
    
    # Sync: Always try to download from GCS to get latest updates
    gcs_handler.download_file(base_gcs, base_path)
    
    if os.path.exists(base_path):
        try:
            with open(base_path, "r", encoding="utf-8") as f:
                base_list = json.load(f)
                if isinstance(base_list, list):
                    base_stopwords = base_stopwords.union(set(base_list))
        except Exception as e:
            print(f"Warning: Could not load base stopwords: {e}")
    
    # Load custom stopwords from file by syncing with GCS
    custom_path = os.path.join("data", media_name, "custom_stopwords.json")
    gcs_path = f"stopwords/{media_name}/custom_stopwords.json"
    
    # Sync: Always download
    gcs_handler.download_file(gcs_path, custom_path)
        
    if os.path.exists(custom_path):
        try:
            with open(custom_path, "r", encoding="utf-8") as f:
                custom_words = json.load(f)
                if isinstance(custom_words, list):
                    base_stopwords = base_stopwords.union(set(custom_words))
        except Exception as e:
            print(f"Warning: Could not load custom stopwords: {e}")

    return base_stopwords
