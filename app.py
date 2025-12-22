from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import model_utils
import train_model
import os
import json

load_dotenv()

app = Flask(__name__)
import gcs_handler

# Cache for loaded models: { "media_name": (model, dictionary) }
loaded_models = {}

def get_or_load_model(media_name):
    if media_name not in loaded_models:
        print(f"Loading model for {media_name}...")
        loaded_models[media_name] = model_utils.load_model(media_name)
    return loaded_models[media_name]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/train', methods=['POST'])
def trigger_train():
    data = request.get_json()
    media = data.get('media', 'edh')
    force = data.get('force', False)
    
    # Trigger training
    result = train_model.train(media, force=force)
    
    if result.get("success"):
        # Clear cache so next prediction reloads the new model
        if media in loaded_models:
            del loaded_models[media]
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/stopwords', methods=['POST'])
def add_stopwords():
    data = request.get_json()
    media = data.get('media', 'edh')
    new_words = data.get('words', [])
    
    if not new_words:
        return jsonify({"success": True, "message": "No words to add."})

    try:
        data_dir = os.path.join("data", media)
        os.makedirs(data_dir, exist_ok=True)
        custom_path = os.path.join(data_dir, "custom_stopwords.json")
        gcs_path = f"stopwords/{media}/custom_stopwords.json"
        
        # Sync: Try to get latest from GCS first to ensure we merge with existing cloud state
        gcs_handler.download_file(gcs_path, custom_path)
        
        current_words = []
        if os.path.exists(custom_path):
            with open(custom_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    current_words = json.loads(content)
        
        # Merge and dedup
        updated_set = set(current_words).union(set(new_words))
        updated_list = list(updated_set)
        
        with open(custom_path, "w", encoding="utf-8") as f:
            json.dump(updated_list, f, ensure_ascii=False, indent=2)
            
        # Sync: Upload back to GCS
        print(f"Uploading updated stopwords to {gcs_path}")
        success = gcs_handler.upload_file(custom_path, gcs_path)
        
        if not success:
            return jsonify({"success": False, "message": "Failed to persist stopwords to GCS."}), 500
            
        return jsonify({"success": True, "message": f"Added {len(new_words)} words to stopwords and synced to GCS."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    text = data.get('text', '')
    media = data.get('media', 'edh') # Default to edh
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    model_tuple = get_or_load_model(media)
    if model_tuple[0] is None:
         return jsonify({'error': f'Model for {media} not found. Please train it first.'}), 404
         
    topics = model_utils.get_topics(model_tuple, text, media)
    return jsonify({'topics': topics, 'media': media})

    topics = model_utils.get_topics(model_tuple, text, media)
    return jsonify({'topics': topics, 'media': media})

@app.route('/model_status/<media>', methods=['GET'])
def model_status(media):
    try:
        versions = gcs_handler.list_model_versions(media)
        if versions:
            # Return true and the latest version
            return jsonify({
                "exists": True, 
                "version": versions[-1],
                "versions": versions
            })
        else:
            return jsonify({"exists": False})
    except Exception as e:
        print(f"Error checking status for {media}: {e}")
        return jsonify({"exists": False, "error": str(e)}), 500

@app.route('/seed_stopwords', methods=['POST'])
def seed_stopwords():
    """
    Admin endpoint to upload local base_stopwords.json to GCS.
    Useful for initializing the bucket from a deployed container.
    """
    try:
        data = request.get_json() or {}
        media = data.get('media', 'edh')
        
        local_path = os.path.join("data", media, "base_stopwords.json")
        gcs_path = f"stopwords/{media}/base_stopwords.json"
        
        if not os.path.exists(local_path):
             return jsonify({"success": False, "message": f"Local file not found: {local_path}"}), 404
             
        success = gcs_handler.upload_file(local_path, gcs_path)
        if success:
            return jsonify({"success": True, "message": f"Seeded {gcs_path}"})
        else:
            return jsonify({"success": False, "message": "Upload failed."}), 500
            
    except Exception as e:
         return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
