import requests
import os
import datetime
import time
from bs4 import BeautifulSoup
from newspaper import Article, Config

# --- CONFIGURATION ---
# No API Key needed for Hacker News/ArXiv! 
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 10

def get_full_article_text(url):
    print(f"    ...Scraping: {url[:50]}...")
    try:
        article = Article(url, config=config)
        article.download()
        article.parse()
        paragraphs = article.text.split('\n')
        html_content = "".join([f"<p>{p.strip()}</p>" for p in paragraphs if len(p.strip()) > 65])
        return html_content if len(html_content) > 500 else None
    except:
        return None

# --- NEW: FETCH TECH-ONLY NEWS VIA HACKER NEWS ---
def fetch_guaranteed_ai_news():
    print("🗞️ Fetching High-Signal AI News from Hacker News...")
    # Searches for 'AI' stories from the last 24 hours with the most points
    url = "https://hn.algolia.com/api/v1/search?query=AI&tags=story&numericFilters=created_at_i>86400"
    
    try:
        response = requests.get(url)
        hits = response.json().get("hits", [])
        
        articles = []
        for hit in hits[:5]: # Take top 5 highest quality stories
            story_url = hit.get('url')
            if not story_url: continue
                
            full_text = get_full_article_text(story_url)
            
            articles.append({
                'title': hit['title'],
                'url': story_url,
                'author': hit['author'],
                'source_name': 'Hacker News Community',
                'content_html': full_text if full_text else f"<p>{hit.get('story_text', 'Click source to read the full discussion and article.')}</p>"
            })
            time.sleep(1)
        return articles
    except Exception as e:
        print(f"Error: {e}")
        return []

def fetch_papers():
    print("🔬 Categorizing ArXiv Research...")
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL&start=0&max_results=6&sortBy=submittedDate&sortOrder=descending"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'xml')
        papers = []
        for entry in soup.find_all('entry'):
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
    except:
        return []

def generate_html(articles, papers):
    today = datetime.datetime.now().strftime("%A, %B %d, %Y").upper()
    
    # Hero Story
    main = articles[0] if articles else {'title': 'Breaking News', 'content_html': 'Loading...', 'author': 'System', 'source_name': 'Internal'}
    
    # Side Stories
    side_html = "".join([f"""
        <div class="side-article">
            <h4>{a['title']}</h4>
            <span class="meta-tag">{a['source_name']}</span>
            <div class="article-body">{a['content_html'][:300]}...</div>
            <a href="{a['url']}" target="_blank" class="read-link">Read Source &rarr;</a>
        </div>""" for a in articles[1:]])

    # Papers
    papers_html = "".join([f"""
        <article class="paper">
            <span class="paper-tag {p['class']}">{p['label']}</span>
            <h4><a href="{p['link']}" target="_blank">{p['title']}</a></h4>
            <p>{p['summary'][:250]}...</p>
        </article>""" for p in papers])

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>The Gemini Gazette</title>
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Merriweather:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {{ --paper: #fdf6e3; --ink: #2c2c2c; --accent: #8b0000; --ai: #1a5f7a; --nlp: #6b4c9a; }}
            body {{ background: #ccc; font-family: 'Merriweather', serif; color: var(--ink); padding: 20px; }}
            .container {{ max-width: 1100px; margin: 0 auto; background: var(--paper); padding: 40px; border: 1px solid #d4cbb8; box-shadow: 10px 10px 0px rgba(0,0,0,0.1); }}
            header {{ text-align: center; border-bottom: 5px double var(--ink); margin-bottom: 30px; }}
            h1 {{ font-family: 'Playfair Display', serif; font-size: 5rem; margin: 0; }}
            .sub-header {{ display: flex; justify-content: space-between; border-top: 2px solid var(--ink); padding: 5px; font-weight: bold; text-transform: uppercase; font-size: 0.8rem; }}
            .main-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 40px; }}
            .dropcap::first-letter {{ font-family: 'Playfair Display', serif; font-size: 4.5rem; float: left; line-height: 0.8; padding-right: 10px; color: var(--accent); }}
            .paper-tag {{ font-family: sans-serif; font-size: 0.6rem; padding: 2px 6px; color: #fff; text-transform: uppercase; }}
            .tag-ai {{ background: var(--ai); }} .tag-nlp {{ background: var(--nlp); }}
            .side-article {{ border-bottom: 1px dotted #999; margin-bottom: 20px; padding-bottom: 10px; }}
            h4 {{ font-family: 'Playfair Display', serif; font-size: 1.4rem; margin: 5px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="sub-header"><span>Vol. 1</span><span>{today}</span><span>AI Special</span></div>
                <h1>The Gemini Gazette</h1>
            </header>
            <div class="main-grid">
                <section>
                    <article>
                        <h2 style="font-family:'Playfair Display'; font-size: 3rem; margin-top:0;">{main['title']}</h2>
                        <p><i>By {main['author']} — {main['source_name']}</i></p>
                        <div class="dropcap">{main['content_html']}</div>
                    </article>
                    <hr style="border: 2px solid var(--ink); margin: 40px 0;">
                    <h3 style="text-transform:uppercase;">Research Deep-Dive</h3>
                    {papers_html}
                </section>
                <aside>
                    <h3 style="border-bottom: 3px solid var(--ink); text-transform:uppercase;">Trending Now</h3>
                    {side_html}
                </aside>
            </div>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    news = fetch_guaranteed_ai_news()
    papers = fetch_papers()
    generate_html(news, papers)
