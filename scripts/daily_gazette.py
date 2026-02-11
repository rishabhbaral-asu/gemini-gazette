import requests
import datetime
import time
import os
from bs4 import BeautifulSoup
from newspaper import Article, Config

# --- CONFIGURATION ---
# IMPORTANT: Ensure your key is valid at https://gnews.io/dashboard
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', 'PASTE_YOUR_KEY_HERE')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 20

def evaluate_content_quality(text, title):
    text_lower = text.lower()
    # Negative filter (The Airfoil Defense)
    kill_keywords = ['aerodynamics', 'fluid dynamics', 'wing design', 'hiring for', 'new role']
    if any(word in text_lower for word in kill_keywords):
        return False, 0

    # Technical Density signals
    signals = {'weights': 3, 'inference': 3, 'transformer': 3, 'quantization': 3, 'dataset': 2, 'llm': 1}
    score = sum(points for word, points in signals.items() if word in text_lower)
    
    # Check for AI-centric title
    ai_title = any(w in title.lower() for w in ['ai', 'intelligence', 'llm', 'model', 'research', 'paperbanana', 'sarvam'])
    return (ai_title or score >= 4), score

def fetch_wide_ai_news():
    print("🌍 Searching Global Web...")
    # Cleaned query for GNews
    query = '("artificial intelligence" OR "machine learning" OR "LLM")'
    url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=20&apikey={GNEWS_API_KEY}"
    
    valid_articles = []
    try:
        resp = requests.get(url)
        print(f"    GNews Status: {resp.status_code}") # Should be 200
        
        if resp.status_code != 200:
            print(f"    GNews Error: {resp.json().get('errors', 'Unknown Error')}")
            return []

        articles_found = resp.json().get('articles', [])
        for entry in articles_found:
            article = Article(entry.get('url'), config=config)
            try:
                article.download()
                article.parse()
                is_good, score = evaluate_content_quality(article.text, entry['title'])
                if is_good:
                    valid_articles.append({
                        'title': entry['title'],
                        'url': entry.get('url'),
                        'author': entry['source']['name'],
                        'source': entry.get('url').split('/')[2],
                        'content': article.text[:800].replace('\n', '<br>'),
                        'score': score
                    })
            except: continue
            if len(valid_articles) >= 5: break
        return valid_articles
    except Exception as e:
        print(f"Request failed: {e}")
        return []

def fetch_arxiv_papers():
    print("🔬 Checking ArXiv (HTTPS Secure)...")
    # Updated to HTTPS and specific AI/Language categories
    url = "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=6"
    headers = {'User-Agent': USER_AGENT}
    
    papers = []
    try:
        res = requests.get(url, headers=headers)
        print(f"    ArXiv Status: {res.status_code}")
        
        soup = BeautifulSoup(res.content, 'xml')
        entries = soup.find_all('entry')
        print(f"    Papers Found: {len(entries)}")
        
        for entry in entries:
            primary = entry.find('arxiv:primary_category')['term']
            papers.append({
                'title': entry.title.text.strip().replace('\n', ' '),
                'summary': entry.summary.text.strip().replace('\n', ' '),
                'link': entry.id.text.strip(),
                'label': "NLP / LANGUAGE" if "cs.CL" in primary else "AI RESEARCH",
                'class': "tag-nlp" if "cs.CL" in primary else "tag-ai"
            })
    except Exception as e:
        print(f"ArXiv Error: {e}")
    return papers

def publish_gazette(news, papers):
    today = datetime.datetime.now().strftime("%A, %B %d, %Y").upper()
    
    # If both lists are empty, the paper needs "Emergency Layout"
    if not news and not papers:
        news = [{'title': "The Signal Is Down", 'url': "#", 'author': "System", 'source': "Local", 'content': "Check your API key and network connection."}]

    news_html = ""
    if news:
        lead = news[0]
        news_html = f"""<div class="lead-story"><h2>{lead['title']}</h2><p class="byline">BY {lead['author']} | {lead['source']}</p><div>{lead['content']}...</div><p><a href="{lead['url']}">Read full report →</a></p></div>"""
        news_html += '<div class="secondary-news">' + "".join([f"<article><h3>{n['title']}</h3><p>{n['content'][:200]}...</p></article>" for n in news[1:]]) + "</div>"

    papers_html = "".join([f"<div class='paper-entry'><span class='tag {p['class']}'>{p['label']}</span><h4><a href='{p['link']}'>{p['title']}</a></h4><p>{p['summary'][:150]}...</p></div><hr>" for p in papers])

    full_html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Libre+Baskerville&display=swap');body {{ background:#f4f1ea; font-family:'Libre Baskerville'; padding:20px; }} .container {{ max-width:1100px; margin:0 auto; background:#fffefc; padding:30px; border:1px solid #333; }} header {{ text-align:center; border-bottom:5px double #333; margin-bottom:20px; }} h1 {{ font-family:'Playfair Display'; font-size:4rem; margin:0; }} main {{ display:grid; grid-template-columns: 2fr 1fr; gap:30px; }} .tag {{ font-size:10px; padding:3px; color:white; background:#333; }} .secondary-news {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; border-top:1px solid #333; padding-top:10px; }}</style></head><body><div class="container"><header><h1>The Gemini Gazette</h1><p>{today}</p></header><main><div>{news_html}</div><aside><h3>RESEARCH WIRE</h3>{papers_html}</aside></main></div></body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print("✅ Gazette Published.")

if __name__ == "__main__":
    publish_gazette(fetch_wide_ai_news(), fetch_arxiv_papers())
