import model_utils
import os

media = "edh"
text = "Effective Weight Loss for Women" # Example text

print(f"--- Debugging '{media}' ---\n")

# 1. Load Model
model, dictionary = model_utils.load_model(media)
if not model:
    print("FATAL: Model could not be loaded.")
    exit(1)

print(f"Dictionary Size: {len(dictionary)}")
print(f"Sample 10 words from dictionary: {list(dictionary.values())[:10]}")

# 2. Test Cleaning
print(f"\nScanning text: '{text}'")
tokens = model_utils.clean_tokens(text.split(), media)
print(f"Cleaned Tokens: {tokens}")

# 3. Test BoW
bow = dictionary.doc2bow(tokens)
print(f"BoW Vector: {bow}")

# 4. Check Intersections
# Manually check if tokens exist in dictionary
for t in tokens:
    try:
        id = dictionary.token2id.get(t)
        print(f"Token '{t}' -> ID: {id}")
    except:
        print(f"Token '{t}' -> NOT IN DICTIONARY")

# 5. Prediction
results = model_utils.get_topics((model, dictionary), text, media)
print(f"\nPrediction Results: {results}")
