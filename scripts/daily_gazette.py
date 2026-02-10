import requests
import os
import datetime
import time
from bs4 import BeautifulSoup
from newspaper import Article, Config

# --- CONFIGURATION ---
# Get your free key at https://newsapi.org
API_KEY = os.environ.get("NEWS_API_KEY") 

# Spoof a real browser to bypass "bot blocks"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 10

# --- 1. THE SCRAPER (newspaper3k) ---
def get_full_article_text(url):
    """
    Intelligently extracts the story body, stripping ads and menus.
    """
    print(f"    ...Attempting full-text extraction: {url[:50]}...")
    try:
        article = Article(url, config=config)
        article.download()
        article.parse()
        
        # Split text into HTML paragraphs
        paragraphs = article.text.split('\n')
        html_content = "".join([f"<p>{p.strip()}</p>" for p in paragraphs if len(p.strip()) > 60])
        
        # If extraction yields too little, return None to trigger fallback
        return html_content if len(html_content) > 400 else None
    except Exception as e:
        print(f"       (!) Extraction failed: {e}")
        return None

# --- 2. FETCH NEWS (Tech/AI) ---
def fetch_news():
    if not API_KEY:
        print("❌ Error: NEWS_API_KEY environment variable not set.")
        return []
    
    print("🗞️ Fetching Daily AI Headlines...")
    url = f"https://newsapi.org/v2/everything?q=artificial+intelligence&language=en&sortBy=publishedAt&apiKey={API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        raw_articles = data.get("articles", [])[:4] # Process top 4
        
        for art in raw_articles:
            full_text = get_full_article_text(art['url'])
            if full_text:
                art['content_html'] = full_text
            else:
                # Fallback to API description if scraping is blocked
                desc = art.get('description') or "Full story available at source."
                art['content_html'] = f"<p>{desc}</p><p><i>(Full content protected by source. Click link to read.)</i></p>"
        
        return raw_articles
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

# --- 3. FETCH & CATEGORIZE PAPERS (ArXiv) ---
def fetch_papers():
    print("🔬 Categorizing ArXiv Research (AI vs NLP)...")
    # Query both AI (cs.AI) and Computation/Language (cs.CL)
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL&start=0&max_results=6&sortBy=submittedDate&sortOrder=descending"
    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'xml')
        entries = soup.find_all('entry')
        
        papers = []
        for entry in entries:
            # Detect primary category
            primary_cat = entry.find('arxiv:primary_category')['term']
            is_nlp = "cs.CL" in primary_cat
            
            papers.append({
                'title': entry.title.text.strip().replace('\n', ' '),
                'summary': entry.summary.text.strip().replace('\n', ' '),
                'link': entry.id.text.strip(),
                'label': "NLP / LANGUAGE" if is_nlp else "AI RESEARCH",
                'class': "tag-nlp" if is_nlp else "tag-ai"
            })
        return papers
    except Exception as e:
        print(f"Error fetching papers: {e}")
        return []

# --- 4. GENERATE HTML ---
def generate_html(articles, papers):
    today = datetime.datetime.now().strftime("%A, %B %d, %Y").upper()
    main_story = articles[0] if articles else None
    side_stories = articles[1:] if articles else []

    # HTML Components
    papers_html = "".join([f"""
        <article class="paper">
            <span class="paper-tag {p['class']}">{p['label']}</span>
            <h4><a href="{p['link']}" target="_blank">{p['title']}</a></h4>
            <p>{p['summary'][:300]}...</p>
        </article>""" for p in papers])

    sidebar_html = "".join([f"""
        <div class="side-article">
            <h4>{s['title']}</h4>
            <span class="meta-tag">{s['source']['name']}</span>
            <div class="article-body">{s['content_html'][:400]}...</div>
            <a href="{s['url']}" target="_blank" class="read-link">Read Full News &rarr;</a>
        </div>""" for s in side_stories])

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>The Gemini Gazette | Live AI Feed</title>
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Merriweather:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
        <style>
            :root {{ --paper: #fdf6e3; --ink: #2c2c2c; --accent: #8b0000; --ai: #1a5f7a; --nlp: #6b4c9a; }}
            body {{ background: #e0e0e0; font-family: 'Merriweather', serif; color: var(--ink); margin: 0; padding: 20px; line-height: 1.6; }}
            .container {{ max-width: 1100px; margin: 0 auto; background: var(--paper); padding: 40px; box-shadow: 0 0 20px rgba(0,0,0,0.2); border: 1px solid #d4cbb8; }}
            header {{ text-align: center; border-bottom: 4px double var(--ink); margin-bottom: 30px; }}
            h1 {{ font-family: 'Playfair Display', serif; font-size: 4.5rem; margin: 10px 0; text-transform: uppercase; }}
            .sub-header {{ display: flex; justify-content: space-between; border-top: 2px solid var(--ink); border-bottom: 1px solid var(--ink); padding: 8px 0; font-size: 0.8rem; font-weight: bold; text-transform: uppercase; }}
            .main-content {{ display: grid; grid-template-columns: 2fr 1fr; gap: 40px; }}
            .hero-article h2 {{ font-family: 'Playfair Display', serif; font-size: 2.8rem; line-height: 1.1; margin-top: 0; }}
            .dropcap::first-letter {{ font-family: 'Playfair Display', serif; font-size: 4rem; float: left; line-height: 0.8; padding-right: 10px; font-weight: 900; color: var(--accent); }}
            .paper-tag {{ font-family: sans-serif; font-size: 0.65rem; padding: 3px 8px; color: white; border-radius: 2px; }}
            .tag-ai {{ background: var(--ai); }} .tag-nlp {{ background: var(--nlp); }}
            .side-article {{ border-bottom: 1px dotted #999; padding-bottom: 15px; margin-bottom: 20px; }}
            a {{ color: var(--accent); text-decoration: none; }}
            @media (max-width: 800px) {{ .main-content {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="sub-header"><span>VOL. II</span><span>{today}</span><span>LIVE AI EDITION</span></div>
                <h1>The Gemini Gazette</h1>
            </header>
            <main class="main-content">
                <section>
                    <article class="hero-article">
                        <h2>{main_story['title'] if main_story else 'No News Found'}</h2>
                        <div class="article-body dropcap">{main_story['content_html'] if main_story else '<p>API limit reached.</p>'}</div>
                    </article>
                    <div style="border-top: 4px double var(--ink); padding-top: 20px; margin-top: 40px;">
                        <h3 style="text-transform: uppercase; font-family: sans-serif;">ArXiv Research Wire</h3>
                        {papers_html}
                    </div>
                </section>
                <aside class="sidebar">
                    <h3 style="border-bottom: 3px solid var(--ink); text-transform: uppercase;">Latest Headlines</h3>
                    {sidebar_html}
                </aside>
            </main>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print("✅ Gazette Published: index.html")

if __name__ == "__main__":
    articles = fetch_news()
    papers = fetch_papers()
    generate_html(articles, papers)
