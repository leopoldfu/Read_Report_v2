import gensim
from gensim.corpora import Dictionary
from gensim.models import LdaModel
import os
import stopwords
import gcs_handler

def clean_tokens(words, media_name="edh"):
    """
    Preprocessing logic.
    """
    stop_words = stopwords.get_stopwords(media_name)
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

def load_model(media_name="edh"):
    """
    Load the LDA model and dictionary for a specific media.
    Returns tuple (model, dictionary)
    """
    model_dir = os.path.join("models", media_name)
    model_path = os.path.join(model_dir, "lda.model")
    dict_path = os.path.join(model_dir, "id2word.dict")

    if not os.path.exists(model_path):
        print(f"Model not found locally for {media_name}. Checking GCS...")
        
        versions = gcs_handler.list_model_versions(media_name)
        if versions:
            latest_version = versions[-1]
            print(f"Found latest version {latest_version} in GCS. Downloading...")
            
            # We download the contents of the version folder into the FLAT local model dir
            success = gcs_handler.download_specific_version(media_name, latest_version, model_dir)
            
            if not success:
                print(f"Failed to download version {latest_version}")
                return None, None
        else:
            print(f"No models found in GCS for {media_name}")
            return None, None
    
    try:
        model = LdaModel.load(model_path)
        if os.path.exists(dict_path):
            dictionary = Dictionary.load(dict_path)
        else:
            print(f"Warning: Dictionary not found at {dict_path}")
            dictionary = None
            
        return model, dictionary
    except Exception as e:
        print(f"Error loading model for {media_name}: {e}")
        return None, None

def get_topics(model_tuple, text_or_tokens, media_name="edh"):
    """
    Get topics for the input.
    """
    model, dictionary = model_tuple
    
    if model is None or dictionary is None:
        return [{"topic_id": -1, "score": 0.0, "words": ["Model not loaded"]}]

    # Preprocessing
    if isinstance(text_or_tokens, str):
         # Normalize using jieba for Chinese segmentation
         import jieba
         tokens = list(jieba.cut(text_or_tokens)) 
    else:
        tokens = text_or_tokens

    clean = clean_tokens(tokens, media_name)
    
    print(f"\n--- Debug Inference for '{media_name}' ---")
    print(f"Input Tokens (Cleaned): {clean}")

    if len(clean) == 0:
        print("Result: No valid tokens.")
        return [{"topic_id": -1, "score": 0.0, "words": ["No valid tokens found (all filtered or unknown)"]}]

    bow = dictionary.doc2bow(clean)
    print(f"BoW Vector (ID, Count): {bow}")
    
    topic_distResult = model.get_document_topics(bow, minimum_probability=0.01)
    print(f"Topic Distribution: {topic_distResult}")
    
    sorted_topics = sorted(topic_distResult, key=lambda x: x[1], reverse=True)
    print(f"Sorted Top 5: {sorted_topics[:5]}")
    print("------------------------------------------\n")
    
    results = []
    for tid, score in sorted_topics[:5]: 
        topic_terms = model.show_topic(tid, topn=10)
        words = [w for w, p in topic_terms]
        results.append({
            "topic_id": tid,
            "score": float(score),
            "words": words
        })
        
    return results

def get_all_topics(model_tuple, topn=40):
    """
    Returns a list of all topics with their top N words.
    """
    model, dictionary = model_tuple
    if model is None:
        return []
    
    # show_topics(num_topics=-1) returns all topics
    raw_topics = model.show_topics(num_topics=-1, num_words=topn, formatted=False)
    
    topics = []
    # raw_topics is list of (topic_id, [(word, prob), ...])
    # However, show_topics sometimes doesn't sort by ID. Let's ensure it is sorted.    
    sorted_raw = sorted(raw_topics, key=lambda x: x[0])

    for tid, words_probs in sorted_raw:
        words = [w for w, p in words_probs]
        topics.append({
            "topic_id": tid,
            "words": words
        })
    return topics
