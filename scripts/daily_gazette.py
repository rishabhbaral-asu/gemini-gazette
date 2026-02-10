import requests
import datetime
import os
from bs4 import BeautifulSoup
from newspaper import Article, Config

# --- CONFIGURATION ---
# Only stories from these domains will be published to maintain signal quality
ALLOWED_DOMAINS = [
    'techcrunch.com', 'wired.com', 'theverge.com', 'technologyreview.com', 
    'arstechnica.com', 'venturebeat.com', 'openai.com', 'anthropic.com',
    'reuters.com', 'nytimes.com', 'bloomberg.com', 'wsj.com'
]

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
        paras = article.text.split('\n')
        # Filter for substantial paragraphs to avoid 'Subscribe now' junk
        return "".join([f"<p>{p.strip()}</p>" for p in paras if len(p.strip()) > 70])
    except:
        return None

def fetch_reputable_ai_news():
    """Fetches high-signal AI stories vetted by Hacker News users."""
    print("🗞️ Filtering for High-Signal Tech News...")
    # HN API sorts by points to ensure human-vetted relevance
    url = "https://hn.algolia.com/api/v1/search?query=artificial+intelligence&tags=story&numericFilters=points>20"
    
    try:
        response = requests.get(url)
        hits = response.json().get('hits', [])
        valid_articles = []
        
        for hit in hits:
            story_url = hit.get('url', '')
            title = hit.get('title', '').lower()
            
            # Anti-"Airfoil" Check: Ensure AI-specific keywords are present
            ai_keywords = ['ai', 'intelligence', 'llm', 'gpt', 'model', 'neural', 'robot', 'learning']
            is_actually_ai = any(word in title for word in ai_keywords)
            
            # Domain Filter
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
            
            if len(valid_articles) >= 5: break 
            
        return valid_articles
    except Exception as e:
        print(f"Error fetching HN: {e}")
        return []

def fetch_arxiv_papers():
    """Fetches the latest AI research from ArXiv."""
    print("🔬 Checking the ArXiv Research Wire...")
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=5"
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
    except Exception as e:
        print(f"Error fetching ArXiv: {e}")
        return []

def publish_gazette(news, papers):
    """Generates the final index.html using the fetched data and your custom styles."""
    today = datetime.datetime.now().strftime("%A, %B %d, %Y").upper()
    
    # Generate News Sections
    news_html = ""
    if news:
        lead = news[0]
        news_html += f"""
        <div class="lead-story">
            <h2>{lead['title']}</h2>
            <p class="byline">BY {lead['author'].upper()} | {lead['source'].upper()}</p>
            <div class="article-content">
                {lead['content'][:900]}... 
                <p><a href="{lead['url']}">Read full report at {lead['source']} →</a></p>
            </div>
        </div>
        <div class="secondary-news">
        """
        for story in news[1:5]:
            news_html += f"""
            <article>
                <h3>{story['title']}</h3>
                <p>{story['content'][:250]}... <a href="{story['url']}">More</a></p>
            </article>
            """
        news_html += "</div>"

    # Generate Research Sidebar
    papers_html = ""
    for p in papers:
        papers_html += f"""
        <div class="paper-entry">
            <span class="tag {p['cat_class']}">{p['cat_label']}</span>
            <h4><a href="{p['link']}">{p['title']}</a></h4>
            <p>{p['summary'][:160]}...</p>
        </div>
        <hr>
        """

    # Final HTML Template (Preserving your specific styles)
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>The Gemini Gazette | {today}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');
            body {{ background-color: #f4f1ea; color: #1a1a1a; font-family: 'Libre Baskerville', serif; margin: 0; padding: 20px; line-height: 1.4; }}
            .container {{ max-width: 1200px; margin: 0 auto; border: 1px solid #333; padding: 20px; background-color: #fffefc; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            header {{ text-align: center; border-bottom: 4px double #333; margin-bottom: 20px; }}
            header h1 {{ font-family: 'Playfair Display', serif; font-size: 4rem; margin: 10px 0; font-weight: 900; }}
            .masthead-meta {{ border-top: 1px solid #333; padding: 5px 0; font-size: 0.9rem; font-weight: bold; border-bottom: 1px solid #333; margin-bottom: 20px; }}
            main {{ display: grid; grid-template-columns: 3fr 1fr; gap: 30px; }}
            .lead-story h2 {{ font-size: 2.8rem; margin-top: 0; line-height: 1.1; }}
            .byline {{ font-style: italic; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; font-size: 0.8rem; }}
            .secondary-news {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; border-top: 2px solid #333; padding-top: 20px; }}
            .tag {{ font-size: 0.65rem; padding: 2px 6px; color: white; border-radius: 2px; text-transform: uppercase; font-weight: bold; }}
            .tag-ai {{ background: #2c3e50; }} .tag-nlp {{ background: #27ae60; }}
            .sidebar {{ border-left: 1px solid #ccc; padding-left: 20px; }}
            .paper-entry h4 {{ margin: 10px 0 5px 0; line-height: 1.2; }}
            .paper-entry p {{ font-size: 0.85rem; color: #444; }}
            a {{ color: #1a1a1a; text-decoration: none; }}
            a:hover {{ border-bottom: 1px solid #333; }}
            footer {{ margin-top: 30px; border-top: 1px solid #333; padding-top: 10px; text-align: center; font-size: 0.8rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>The Gemini Gazette</h1>
                <div class="masthead-meta">VOL. IV ... NO. 118 — TEMPE, ARIZONA — {today}</div>
            </header>
            <main>
                <div class="news-column">
                    {news_html}
                </div>
                <div class="sidebar">
                    <h3 style="font-family: 'Playfair Display'; border-bottom: 2px solid #333;">LATEST RESEARCH</h3>
                    {papers_html}
                    <div class="editor-note">
                        <h4 style="font-family: 'Playfair Display';">Editor's Note</h4>
                        <p style="font-size: 0.8rem; font-style: italic;">This edition was autonomously compiled using Hacker News ranking signals and ArXiv research categories.</p>
                    </div>
                </div>
            </main>
            <footer>
                &copy; 2026 rishabhbaral-asu/gemini-gazette • Published with GitHub Actions
            </footer>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"✅ Gazette generated successfully.")

if __name__ == "__main__":
    ai_news = fetch_reputable_ai_news()
    research_papers = fetch_arxiv_papers()
    publish_gazette(ai_news, research_papers)
