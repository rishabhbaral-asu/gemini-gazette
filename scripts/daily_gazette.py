import requests
import datetime
import time
import os
from bs4 import BeautifulSoup
from newspaper import Article, Config

# --- CONFIGURATION ---
# High-signal domains. We also allow high-scoring stories from unknown domains 
# IF they pass our technical content score.
ALLOWED_DOMAINS = [
    'techcrunch.com', 'wired.com', 'theverge.com', 'technologyreview.com', 
    'arstechnica.com', 'venturebeat.com', 'openai.com', 'anthropic.com',
    'reuters.com', 'nytimes.com', 'bloomberg.com', 'wsj.com', 'sarvam.ai', 'paperbanana.com'
]

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 15

def evaluate_content_quality(text, title):
    """
    Heuristic to separate 'AI Advancement/Research' from 'Social Fluff'.
    Returns (is_quality: bool, score: int)
    """
    text_lower = text.lower()
    
    # 🛑 REJECTION CRITERIA: Common social media/job announcement fluff
    noise_triggers = [
        "excited to announce", "hiring for", "joined the team", 
        "my new role", "looking for a job", "honored to be part",
        "personal news", "happy to share"
    ]
    if any(trigger in text_lower for trigger in noise_triggers):
        return False, 0

    # 🔬 SIGNAL CRITERIA: Technical density points
    signals = {
        'weights': 3, 'parameters': 3, 'inference': 2, 'latency': 2, 
        'benchmark': 2, 'transformer': 2, 'dataset': 2, 'gpu': 1,
        'token': 1, 'quantization': 2, 'fine-tuning': 2, 'architecture': 1,
        'open-source': 1, 'sota': 2, 'throughput': 2
    }
    
    score = sum(points for word, points in signals.items() if word in text_lower)
    
    # Minimum score threshold for publication
    # Labs like Sarvam AI or PaperBanana usually hit 6+ points easily.
    return (score >= 4), score

def fetch_reputable_ai_news():
    print("🗞️ Scraping LATEST High-Signal News...")
    
    # FIX: Only look at stories from the last 48 hours to avoid 2020 results
    time_window = int(time.time()) - (48 * 3600)
    
    # Using 'search_by_date' ensures chronological relevance
    url = f"https://hn.algolia.com/api/v1/search_by_date?query=AI&tags=story&numericFilters=created_at_i>{time_window}"
    
    try:
        response = requests.get(url)
        hits = response.json().get('hits', [])
        valid_articles = []
        
        for hit in hits:
            story_url = hit.get('url', '')
            if not story_url: continue
                
            domain = story_url.split('/')[2].replace('www.', '')
            
            # Layer 1: Check if domain is trusted OR if the community upvoted it heavily
            if any(d in domain for d in ALLOWED_DOMAINS) or hit.get('points', 0) > 40:
                
                # Layer 2: Download and Read the article
                article = Article(story_url, config=config)
                try:
                    article.download()
                    article.parse()
                    
                    # Layer 3: Technical Quality Scoring
                    is_quality, score = evaluate_content_quality(article.text, hit['title'])
                    
                    if is_quality:
                        print(f"    [VERIFIED - Score {score}]: {hit['title']}")
                        valid_articles.append({
                            'title': hit['title'],
                            'url': story_url,
                            'author': hit['author'],
                            'source': domain,
                            'content': article.text,
                            'score': score
                        })
                    else:
                        print(f"    [REJECTED - Fluff]: {hit['title']}")
                except:
                    continue
            
            if len(valid_articles) >= 5: break
            
        return valid_articles
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def fetch_arxiv_papers():
    """Fetches the latest research, distinguishing cs.AI from cs.CL."""
    print("🔬 Checking ArXiv Research Wire...")
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
                'label': "NLP / LANGUAGE" if "cs.CL" in primary else "AI RESEARCH",
                'class': "tag-nlp" if "cs.CL" in primary else "tag-ai"
            })
        return papers
    except:
        return []

def publish_gazette(news, papers):
    today = datetime.datetime.now().strftime("%A, %B %d, %Y").upper()
    
    # Hero & Secondary News Construction
    news_html = ""
    if news:
        lead = news[0]
        news_html += f"""
        <div class="lead-story">
            <h2>{lead['title']}</h2>
            <p class="byline">BY {lead['author'].upper()} | {lead['source'].upper()}</p>
            <div class="article-content">{lead['content'][:1000].replace('\\n', '<br>')}...</div>
            <p><a href="{lead['url']}">Read full report →</a></p>
        </div>
        <div class="secondary-news">
        """
        for story in news[1:]:
            news_html += f"""
            <article>
                <h3>{story['title']}</h3>
                <p>{story['content'][:280]}... <a href="{story['url']}">More</a></p>
            </article>
            """
        news_html += "</div>"

    # Sidebar Construction
    papers_html = "".join([f"""
        <div class="paper-entry">
            <span class="tag {p['class']}">{p['label']}</span>
            <h4><a href="{p['link']}">{p['title']}</a></h4>
            <p>{p['summary'][:180]}...</p>
        </div><hr>""" for p in papers])

    # Final Template
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>The Gemini Gazette</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');
            body {{ background-color: #f4f1ea; color: #1a1a1a; font-family: 'Libre Baskerville', serif; margin: 0; padding: 20px; }}
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
                <div class="masthead-meta">TEMPE, AZ — {today} — LATEST AI & RESEARCH WIRE</div>
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
    news = fetch_reputable_ai_news()
    papers = fetch_arxiv_papers()
    publish_gazette(news, papers)
