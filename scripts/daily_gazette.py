import requests
import datetime
import time
import os
from bs4 import BeautifulSoup
from newspaper import Article, Config

# --- CONFIGURATION ---
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', 'PASTE_YOUR_KEY_HERE')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 15

def evaluate_content_quality(text, title):
    """The Technical Gatekeeper: Filters out Airfoils, Jobs, and Fluff."""
    text_lower = text.lower()
    
    # 1. IMMEDIATE KILL LIST (Non-AI tech and Social Fluff)
    kill_keywords = [
        'aerodynamics', 'fluid dynamics', 'wing design', 'lift coefficient',
        'excited to announce', 'honored to join', 'hiring for', 'new role'
    ]
    if any(word in text_lower for word in kill_keywords):
        return False, 0

    # 2. AI SIGNAL SCORING
    signals = {
        'weights': 3, 'parameters': 3, 'inference': 3, 'transformer': 3,
        'quantization': 3, 'dataset': 2, 'benchmark': 2, 'latency': 2,
        'tokenization': 2, 'fine-tuning': 2, 'llm': 1, 'architecture': 1
    }
    
    score = sum(points for word, points in signals.items() if word in text_lower)
    
    # Must mention AI/Research in title AND have technical body score
    ai_title = any(w in title.lower() for w in ['ai', 'intelligence', 'llm', 'model', 'research', 'sarvam', 'paperbanana'])
    
    return (ai_title and score >= 4), score

def fetch_wide_ai_news():
    """Searches the entire web via GNews and picks the best 50 to read."""
    print("🌍 Searching the global web for AI advancements...")
    
    # Query for broad but relevant AI terms
    query = '"artificial intelligence" OR "LLM" OR "AI model" OR "machine learning"'
    url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=50&apikey={GNEWS_API_KEY}"
    
    valid_articles = []
    try:
        response = requests.get(url).json()
        articles_found = response.get('articles', [])
        
        for entry in articles_found:
            story_url = entry.get('url')
            article = Article(story_url, config=config)
            
            try:
                article.download()
                article.parse()
                
                is_quality, score = evaluate_content_quality(article.text, entry['title'])
                
                if is_quality:
                    # Pre-clean for f-string safety
                    clean_content = article.text[:1000].replace('\n', '<br>')
                    valid_articles.append({
                        'title': entry['title'],
                        'url': story_url,
                        'author': entry['source']['name'],
                        'source': story_url.split('/')[2].replace('www.', ''),
                        'content': clean_content,
                        'score': score
                    })
                    print(f"    [PICKED - Score {score}]: {entry['title']}")
            except:
                continue
            
            if len(valid_articles) >= 6: break
            
        return sorted(valid_articles, key=lambda x: x['score'], reverse=True)
    except Exception as e:
        print(f"GNews Error: {e}")
        return []

def fetch_arxiv_papers():
    """ArXiv remains the gold standard for formal papers."""
    print("🔬 Checking ArXiv Research Wire...")
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=6"
    papers = []
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.content, 'xml')
        for entry in soup.find_all('entry'):
            primary = entry.find('arxiv:primary_category')['term']
            papers.append({
                'title': entry.title.text.strip().replace('\n', ' '),
                'summary': entry.summary.text.strip().replace('\n', ' '),
                'link': entry.id.text.strip(),
                'label': "NLP / LANGUAGE" if "cs.CL" in primary else "AI RESEARCH",
                'class': "tag-nlp" if "cs.CL" in primary else "tag-ai"
            })
    except: pass
    return papers

def publish_gazette(news, papers):
    today = datetime.datetime.now().strftime("%A, %B %d, %Y").upper()
    
    # Logic to build HTML (same as previous, ensuring lead content is cleaned)
    news_html = ""
    if news:
        lead = news[0]
        news_html += f"""
        <div class="lead-story">
            <h2>{lead['title']}</h2>
            <p class="byline">BY {lead['author'].upper()} | {lead['source'].upper()}</p>
            <div class="article-content">{lead['content']}...</div>
            <p><a href="{lead['url']}">Read full report →</a></p>
        </div>
        <div class="secondary-news">"""
        for story in news[1:5]:
            news_html += f"""
            <article>
                <h3>{story['title']}</h3>
                <p>{story['content'][:250]}... <a href="{story['url']}">More</a></p>
            </article>"""
        news_html += "</div>"

    papers_html = "".join([f"""
        <div class="paper-entry">
            <span class="tag {p['class']}">{p['label']}</span>
            <h4><a href="{p['link']}">{p['title']}</a></h4>
            <p>{p['summary'][:180]}...</p>
        </div><hr>""" for p in papers])

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>The Gemini Gazette</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');
            body {{ background-color: #f4f1ea; color: #1a1a1a; font-family: 'Libre Baskerville', serif; margin: 0; padding: 20px; line-height: 1.5; }}
            .container {{ max-width: 1200px; margin: 0 auto; border: 1px solid #333; padding: 25px; background: #fffefc; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            header {{ text-align: center; border-bottom: 5px double #333; margin-bottom: 25px; }}
            header h1 {{ font-family: 'Playfair Display', serif; font-size: 4.5rem; margin: 5px 0; }}
            .masthead-meta {{ border-top: 1px solid #333; padding: 5px 0; font-size: 0.85rem; font-weight: bold; border-bottom: 1px solid #333; margin-bottom: 20px; }}
            main {{ display: grid; grid-template-columns: 3fr 1fr; gap: 40px; }}
            .tag {{ font-size: 0.6rem; padding: 2px 6px; color: white; border-radius: 2px; text-transform: uppercase; font-weight: bold; }}
            .tag-ai {{ background: #2c3e50; }} .tag-nlp {{ background: #27ae60; }}
            .secondary-news {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; border-top: 2px solid #333; padding-top: 20px; }}
            .sidebar {{ border-left: 1px solid #ccc; padding-left: 20px; }}
            a {{ color: #1a1a1a; text-decoration: none; border-bottom: 1px dotted #999; }}
            h2, h3 {{ font-family: 'Playfair Display', serif; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>The Gemini Gazette</h1>
                <div class="masthead-meta">TEMPE, AZ — {today} — GLOBAL AI SCOUT</div>
            </header>
            <main>
                <div class="news-column">{news_html}</div>
                <div class="sidebar">
                    <h3 style="border-bottom: 2px solid #333;">RESEARCH WIRE</h3>
                    {papers_html}
                </div>
            </main>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print("✅ Gazette Published.")

if __name__ == "__main__":
    news_data = fetch_wide_ai_news()
    paper_data = fetch_arxiv_papers()
    publish_gazette(news_data, paper_data)
