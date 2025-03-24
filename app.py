from flask import Flask, render_template, request
from crawler import search_papers  # Import from crawler.py

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    results = []  # List to hold the search results
    query = None  # No query by default

    # For GET request (initial page load), load all papers
    if request.method == "GET":
        results = search_papers("")  # Passing an empty string loads all papers

    # For POST request (search), filter based on query
    if request.method == "POST":
        query = request.form["query"].strip()
        results = search_papers(query)

    return render_template("index.html", papers=results, query=query)

if __name__ == "__main__":
    app.run(debug=True)
