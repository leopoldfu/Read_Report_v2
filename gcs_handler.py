import os
from google.cloud import storage

def get_bucket_name():
    return os.environ.get("GCS_BUCKET_NAME")

def get_keys_blobs(bucket, prefix):
    """
    Helper to list all blobs with a prefix
    """
    return list(bucket.list_blobs(prefix=prefix))

def upload_folder(local_folder, gcs_path):
    """
    Uploads a local folder to a GCS path.
    Example: local_folder='models/edh', gcs_path='models/edh/20230101'
    """
    bucket_name = get_bucket_name()
    if not bucket_name:
        print("GCS_BUCKET_NAME not set. Skipping upload.")
        return

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        print(f"Uploading {local_folder} to gs://{bucket_name}/{gcs_path} ...")
        
        # Walk through the directory
        for root, dirs, files in os.walk(local_folder):
            for file in files:
                local_file_path = os.path.join(root, file)
                
                # Calculate relative path from local_folder
                relative_path = os.path.relpath(local_file_path, local_folder)
                
                # Construct blob path
                blob_path = os.path.join(gcs_path, relative_path)
                
                blob = bucket.blob(blob_path)
                blob.upload_from_filename(local_file_path)
        
        print(f"Successfully uploaded.")
    except Exception as e:
        print(f"Failed to upload to GCS: {e}")

def list_model_versions(media):
    """
    Returns a sorted list of version strings (timestamps) found in GCS for a media.
    Assumes structure: models/{media}/{timestamp}/...
    """
    bucket_name = get_bucket_name()
    if not bucket_name:
        return []

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        prefix = f"models/{media}/"
        
        # We need to simulate directory listing.
        # delimiter='/' makes it return 'prefixes' (subdirectories)
        blobs = bucket.list_blobs(prefix=prefix, delimiter='/')
        
        # Force iteration to populate prefixes
        list(blobs)
        
        versions = []
        for p in blobs.prefixes:
            # p is like 'models/edh/20231222_120000/'
            # extract the last part
            parts = p.rstrip('/').split('/')
            if parts:
                versions.append(parts[-1])
                
        versions.sort()
        return versions
    except Exception as e:
        print(f"Error listing versions: {e}")
        return []

def download_specific_version(media, version, local_destination):
    """
    Downloads models/{media}/{version}/* to local_destination
    """
    bucket_name = get_bucket_name()
    if not bucket_name:
        return False
        
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        gcs_prefix = f"models/{media}/{version}/"
        
        blobs = bucket.list_blobs(prefix=gcs_prefix)
        
        count = 0
        for blob in blobs:
            if blob.name.endswith("/"): continue
            
            # relpath inside the version folder
            # blob.name = models/edh/2023.../lda.model
            # rel = lda.model
            relative_path = blob.name[len(gcs_prefix):] 
            
            local_path = os.path.join(local_destination, relative_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            blob.download_to_filename(local_path)
            count += 1
            
        return count > 0
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def delete_version(media, version):
    """
    Deletes models/{media}/{version}/ recursively
    """
    bucket_name = get_bucket_name()
    if not bucket_name:
        return

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        prefix = f"models/{media}/{version}/"
        
        blobs = list(bucket.list_blobs(prefix=prefix))
        if not blobs:
            return
            
        bucket.delete_blobs(blobs)
        print(f"Deleted old version: {version}")
    except Exception as e:
        print(f"Failed to delete version {version}: {e}")

def upload_file(local_path, gcs_path):
    """
    Uploads a single file to GCS.
    """
    bucket_name = get_bucket_name()
    if not bucket_name:
        return
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(local_path)
        print(f"Uploaded {local_path} to gs://{bucket_name}/{gcs_path}")
        return True
    except Exception as e:
        print(f"Failed to upload file to GCS: {e}")
        return False

def download_file(gcs_path, local_destination):
    """
    Downloads a single file from GCS to local_destination.
    """
    bucket_name = get_bucket_name()
    if not bucket_name:
        return False
        
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        
        if not blob.exists():
            return False
            
        blob.download_to_filename(local_destination)
        print(f"Downloaded gs://{bucket_name}/{gcs_path} to {local_destination}")
        return True
    except Exception as e:
        print(f"Failed to download file from GCS: {e}")
        return False
