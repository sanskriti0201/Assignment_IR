import tkinter as tk
from tkinter import messagebox
import feedparser
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE

# Download necessary NLTK resources
def download_nltk_resources():
    nltk.download('stopwords')
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    nltk.download('punkt_tab')

download_nltk_resources()

# Function for text preprocessing
def preprocess_text(text):
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special characters
    words = word_tokenize(text)  # Tokenization
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words]  # Remove stopwords
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words]  # Lemmatization
    return ' '.join(words)

# Fetch articles from RSS feeds
def fetch_articles_from_rss(url, category, num_articles=50):
    articles = []
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            print(f"No articles found in the RSS feed for {category}.")
            return articles
        for entry in feed.entries[:num_articles]:
            article_title = entry.title
            article_summary = entry.summary if 'summary' in entry else ""
            article_text = f"{article_title}. {article_summary}".strip()
            articles.append({"text": article_text, "category": category})
    except Exception as e:
        print(f"Error fetching articles from {url}: {e}")
    return articles

# RSS Feeds for Categories
rss_feeds = {
    "Politics": [
        "http://feeds.bbci.co.uk/news/politics/rss.xml",
        "https://www.theguardian.com/politics/rss",
        "https://rss.politico.com/politics-news.xml",
        "http://www.borntorunthenumbers.com/feeds/posts/default?alt=rss"
        "https://feeds.skynews.com/feeds/rss/politics.xml"
    ],
    "Business": [
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "https://www.cnbc.com/id/10001147/device/rss/rss.html",
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
    ],
    "Health": [
        "http://feeds.bbci.co.uk/news/health/rss.xml",
        "https://www.medicinenet.com/rss/dailyhealth.xml",
        "https://www.medicinenet.com/rss/dailyhealth.xml",
        "https://www.who.int/rss-feeds/news-english.xml"
    ]
}

# Fetch articles
data = []
for category, urls in rss_feeds.items():
    for url in urls:
        print(f"Fetching {category} articles from RSS feed: {url}")
        articles = fetch_articles_from_rss(url, category, num_articles=50)
        print(f"Fetched {len(articles)} {category} articles.")
        data.extend(articles)

df = pd.DataFrame(data)

# Remove duplicates and empty rows
df.drop_duplicates(subset=["text"], inplace=True)
df.dropna(inplace=True)

# Apply preprocessing
df['clean_text'] = df['text'].apply(preprocess_text)

# Balance the dataset
min_articles = df['category'].value_counts().min()
df_balanced = df.groupby('category', group_keys=False).apply(lambda x: x.sample(min_articles, random_state=42, replace=True))

# Convert text data to features using TF-IDF
vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
X = vectorizer.fit_transform(df_balanced['clean_text'])
y = df_balanced['category']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Apply SMOTE to balance classes
smote = SMOTE(random_state=42)
X_train_res, y_train_res = smote.fit_resample(X_train, y_train)

# Train model with balanced class weights using SMOTE
model = LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000)
model.fit(X_train_res, y_train_res)

# Evaluate model
y_pred = model.predict(X_test)
print("Model Accuracy:", accuracy_score(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))

# Tkinter GUI for classification
def classify_document():
    user_input = text_input.get("1.0", "end-1c").strip()
    if not user_input:
        messagebox.showwarning("Input Error", "Please enter a document.")
        return
    text_vector = vectorizer.transform([preprocess_text(user_input)])
    prediction = model.predict(text_vector)[0]
    messagebox.showinfo("Classification Result", f"Category: {prediction}")

# Build GUI
root = tk.Tk()
root.title("Document Classification System")

label = tk.Label(root, text="Enter a document to classify it into Politics, Business, or Health:")
label.pack(pady=10)

text_input = tk.Text(root, height=10, width=50)
text_input.pack(pady=10)

classify_button = tk.Button(root, text="Classify", command=classify_document)
classify_button.pack(pady=10)

root.mainloop()
