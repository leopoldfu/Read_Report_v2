import gcs_handler
import os

def sync_base_stopwords(media="edh"):
    local_path = f"data/{media}/base_stopwords.json"
    gcs_path = f"stopwords/{media}/base_stopwords.json"
    
    if os.path.exists(local_path):
        print(f"Uploading {local_path} to {gcs_path}...")
        success = gcs_handler.upload_file(local_path, gcs_path)
        if success:
            print("Upload successful.")
        else:
            print("Upload failed.")
    else:
        print(f"File not found: {local_path}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    sync_base_stopwords("edh")
