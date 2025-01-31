# Importing the libraries
import numpy as np
import joblib
import re, string
import requests
# import nltk
# nltk.download("stopwords")
# nltk.download('punkt')
# nltk.download('wordnet')
from nltk.corpus import stopwords
stop_words = set(stopwords.words("english"))
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer 
from scipy.sparse import hstack
from flask import Flask, request, jsonify, render_template, url_for
from bs4 import BeautifulSoup

app = Flask(__name__)

# Creating a function to clean the training dataset
def clean_text(text):
    """This function will take text as input and return a cleaned text 
        by removing html char, punctuations, non-letters, newline and converting it 
        to lower case.
    """
    # Converting to lower case letters
    text = text.lower()
    # Removing the contraction of few words
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"can't", "can not ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r"\'scuse", " excuse ", text)
    # Replacing the HTMl characters with " "
    text = re.sub("<.*?>", " ", text)
    # Removing the punctuations
    text = text.translate(str.maketrans(" ", " ", string.punctuation))
    # Removing non-letters
    text = re.sub("[^a-zA-Z]", " ", text)
    # Replacing newline with space
    text = re.sub("\n", " ", text)
    # Split on space and rejoin to remove extra spaces
    text = " ".join(text.split())
    
    return text

def word_lemmatizer(text):
    """This function will help lemmatize words in a text.
    """
    
    lemmatizer = WordNetLemmatizer()
    # Tokenize the sentences to words
    text = word_tokenize(text)
    # Removing the stop words
    text = [lemmatizer.lemmatize(word) for word in text]
    # Joining the cleaned list
    text = " ".join(text)
    
    return text

# Loading the TFIF vectorizers
word_tfidf = joblib.load("models/word_tfidf_vectorizer.pkl")
char_tfidf = joblib.load("models/char_tfidf_vectorizer.pkl")

# Loading the LR models for each label
lr_toxic = joblib.load("models/logistic_regression_toxic.pkl")
lr_severe = joblib.load("models/logistic_regression_severe_toxic.pkl")
lr_obscene = joblib.load("models/logistic_regression_obscene.pkl")
lr_threat = joblib.load("models/logistic_regression_threat.pkl")
lr_insult = joblib.load("models/logistic_regression_insult.pkl")
lr_identity = joblib.load("models/logistic_regression_identity_hate.pkl")

# Render the HTML file for home page
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    # Accept the text as user input
    text_input = request.form["text"]
    text_cleaned = clean_text(text_input)
    text_data = word_lemmatizer(text_cleaned)
    
    input = [text_data]
    
    # Transforming to TF-IDF vectors
    word_features = word_tfidf.transform(input)
    char_features = char_tfidf.transform(input)
    all_features = hstack([word_features, char_features])
    
    # Predicting for each target variable
    pred_toxic = np.round(lr_toxic.predict_proba(all_features)[:,1], 2)*100
    pred_severe_toxic = np.round(lr_severe.predict_proba(all_features)[:,1], 2)*100
    pred_obscene = np.round(lr_obscene.predict_proba(all_features)[:,1], 2)*100
    pred_threat = np.round(lr_threat.predict_proba(all_features)[:,1], 2)*100
    pred_insult = np.round(lr_insult.predict_proba(all_features)[:,1], 2)*100
    pred_identity = np.round(lr_identity.predict_proba(all_features)[:,1], 2)*100
    
    # Creating a dictionary for rendering the table
    predictions = {
        "Toxic": f"{' '.join(map(str, pred_toxic))} %",
        "Severe Toxic": f"{' '.join(map(str, pred_severe_toxic))} %",
        "Obscene": f"{' '.join(map(str, pred_obscene))} %",
        "Threat": f"{' '.join(map(str, pred_threat))} %",
        "Insult": f"{' '.join(map(str, pred_insult))} %",
        "Identity Hate": f"{' '.join(map(str, pred_identity))} %"
    }
    
    # Defining a threshold for toxicity
    threshold = 50
    
    # Check if any of the prediction values exceed the threshold
    toxic_score = max(pred_toxic, pred_severe_toxic, pred_obscene, pred_threat, pred_insult, pred_identity)
    
    # If any prediction exceeds the threshold, classify as "Toxic"
    if toxic_score > threshold:
        toxicity_label = "Toxic"
    else:
        toxicity_label = "Normal"

    return render_template("index.html",
                           comment_text=f"Your input comment: {text_input}",
                           predictions=predictions,
                           toxicity_label=toxicity_label)

    
if __name__ == "__main__":
    app.run(debug=True)    

# # For AWS
# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=8080)