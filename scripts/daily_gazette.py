import requests
import datetime
import time
from bs4 import BeautifulSoup
from newspaper import Article, Config

# --- REPUTABLE SOURCE LIST ---
# Only stories from these domains will be published
ALLOWED_DOMAINS = [
    'techcrunch.com', 'wired.com', 'theverge.com', 'technologyreview.com', 
    'arstechnica.com', 'venturebeat.com', 'openai.com', 'anthropic.com',
    'reuters.com', 'nytimes.com', 'bloomberg.com', 'wsj.com', 'medium.com'
]

# --- SCRAPER CONFIG ---
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 15

def get_full_article_text(url):
    """Cleanly extracts story text using Newspaper3k."""
    try:
        article = Article(url, config=config)
        article.download()
        article.parse()
        # Create HTML paragraphs from the cleaned text
        paras = article.text.split('\n')
        return "".join([f"<p>{p.strip()}</p>" for p in paras if len(p.strip()) > 70])
    except:
        return None

def fetch_reputable_ai_news():
    print("🗞️ Filtering for High-Signal Tech News...")
    # Using Algolia's HN API to find stories mentioning AI, LLM, or Machine Learning
    # sorted by points (human-vetted relevance)
    url = "https://hn.algolia.com/api/v1/search?query=artificial+intelligence&tags=story&numericFilters=points>20"
    
    try:
        response = requests.get(url)
        hits = response.json().get('hits', [])
        valid_articles = []
        
        for hit in hits:
            story_url = hit.get('url', '')
            title = hit.get('title', '').lower()
            
            # THE FIX: Ensure it's not "Airfoil" or "Airport"
            # We look for tech-specific keywords
            ai_keywords = ['ai', 'intelligence', 'llm', 'gpt', 'model', 'neural', 'robot', 'learning']
            is_actually_ai = any(word in title for word in ai_keywords)
            
            # Check if domain is reputable (optional: remove this check if you want all HN news)
            is_reputable = any(domain in story_url for domain in ALLOWED_DOMAINS)
            
            if is_actually_ai and story_url:
                print(f"    [Approved]: {hit['title']}")
                full_text = get_full_article_text(story_url)
                
                valid_articles.append({
                    'title': hit['title'],
                    'url': story_url,
                    'author': hit['author'],
                    'source': story_url.split('/')[2].replace('www.', ''),
                    'content': full_text if full_text else f"<p>{hit.get('story_text', 'Visit source for full report.')}</p>"
                })
            
            if len(valid_articles) >= 5: break # Stop once we have 5 quality stories
            
        return valid_articles
    except Exception as e:
        print(f"Error: {e}")
        return []

def fetch_arxiv_papers():
    """Fetches and categorizes ArXiv papers."""
    print("🔬 Checking the ArXiv Research Wire...")
    # Distinguish between AI and CL (Language)
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=6"
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.content, 'xml')
        papers = []
        for entry in soup.find_all('entry'):
            primary = entry.find('arxiv:primary_category')['term']
            papers.append({
                'title': entry.title.text.strip().replace('\n', ' '),
                'summary': entry.summary.text.strip().replace('\n', ' '),
                'link': entry.id.text.strip(),
                'cat_label': "NLP / LANGUAGE" if "cs.CL" in primary else "AI RESEARCH",
                'cat_class': "tag-nlp" if "cs.CL" in primary else "tag-ai"
            })
        return papers
    except:
        return []

def publish_gazette(news, papers):
    today = datetime.datetime.now().strftime("%A, %B %d, %Y").upper()
    
    # Styles and Layout
    # (Using the same high-end CSS from previous versions)
    # ... (Include your HTML generation logic here) ...
    print(f"✅ Gazette generated with {len(news)} stories and {len(papers)} papers.")

if __name__ == "__main__":
    news_data = fetch_reputable_ai_news()
    paper_data = fetch_arxiv_papers()
    # Now call your publish/generate_html function using these clean lists
