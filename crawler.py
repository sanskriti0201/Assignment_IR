import time
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
from whoosh.query import Every, Or
from whoosh.index import open_dir

INDEX_DIR = "index"


# Function to create search index
def create_index(papers):
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)

    schema = Schema(
        title=TEXT(stored=True),
        link=ID(stored=True),
        date=TEXT(stored=True),
        authors=TEXT(stored=True)  # Added authors field to schema
    )
    ix = create_in(INDEX_DIR, schema)
    writer = ix.writer()

    for paper in papers:
        # Convert authors list to a JSON string
        authors_json = json.dumps(paper["authors"])
        writer.add_document(
            title=paper["title"],
            link=paper["link"],
            date=paper["date"],
            authors=authors_json  # Store authors as a JSON string
        )
    writer.commit()


# Function to search papers
def search_papers(query):
    try:
        ix = open_dir("index")  # Ensure index directory is correct
        with ix.searcher() as searcher:
            if query.strip():  # If user entered a query, search for it
                # Parse query for title and authors
                title_parser = QueryParser("title", ix.schema)
                author_parser = QueryParser("authors", ix.schema)

                title_query = title_parser.parse(query)
                author_query = author_parser.parse(query)

                # Combine both queries (using OR, so it searches for either title or authors)
                combined_query = Or([title_query, author_query])

            else:  # If no query, return all results
                combined_query = Every("title")

            results = searcher.search(combined_query, limit=20)  # Get max 20 results
            return [
                {
                    "title": r["title"],
                    "link": r["link"],
                    "date": r["date"],
                    "authors": json.loads(r["authors"])  # Convert the JSON string back to a list
                } for r in results
            ]

    except Exception as e:
        print(f"Search error: {e}")
        return []


# Function to crawl publications
def crawl_publications():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    URL = "https://pureportal.coventry.ac.uk/en/organisations/fbl-school-of-economics-finance-and-accounting/publications/"
    driver.get(URL)

    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "list-results")))
    except:
        print("Timeout: Could not find research papers.")
        driver.quit()
        return []

    scroll_pause_time = 2
    for _ in range(15):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    research_papers = []
    results = soup.find_all("li", class_="list-result-item")

    for res in results:
        title_tag = res.find("h3", class_="title")
        if title_tag:
            title = title_tag.text.strip()
            link_tag = title_tag.find("a")
            link = link_tag["href"] if link_tag else "No link available"
            if link and not link.startswith("http"):
                link = "https://pureportal.coventry.ac.uk" + link

            authors = []
            author_tags = res.find_all(name="a", class_="link person")  # Find all author tags

            for author_tag in author_tags:
                author_name = author_tag.text.strip() # Extract author name
                if not author_name:
                    continue   # Skip if the author name is empty
                author_profile_link = author_tag.get("href", "").strip()  # Skip if the author name is empty
                if not author_profile_link:             # Skip if the profile link is empty
                    continue
                if not author_profile_link.startswith(("http://", "https://")):
                    author_profile_link = "https://pureportal.coventry.ac.uk" + author_profile_link   # Ensure validity of URL
                # Append the author details to the list
                authors.append({"name": author_name, "profile_link": author_profile_link})

            date_tag = res.find("span", class_="date")
            publication_date = date_tag.text.strip() if date_tag else "Unknown"

            paper_data = {
                "title": title,
                "link": link,
                "authors": authors,  # Store authors as a list of dictionaries
                "date": publication_date,
            }
            research_papers.append(paper_data)

    return research_papers


if __name__ == "__main__":
    print("Crawling publications...")
    papers = crawl_publications()
    create_index(papers)
    print(f"Indexed {len(papers)} research papers.")
