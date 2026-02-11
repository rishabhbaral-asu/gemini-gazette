import requests
import datetime
import time
from bs4 import BeautifulSoup
from newspaper import Article, Config

# --- CONFIGURATION ---
# We still keep these for "Bonus Points", but we no longer limit to them.
RESEARCH_LABS = ['openai.com', 'anthropic.com', 'sarvam.ai', 'paperbanana.com']
GNEWS_API_KEY = "YOUR_GNEWS_API_KEY" # Add this to your GitHub Secrets!

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 10

def evaluate_content_quality(text, domain):
    text_lower = text.lower()
    
    # Direct Pass for known high-signal labs
    if any(lab in domain for lab in RESEARCH_LABS):
        return True, 100

    # Strict "No Fluff" Filter
    noise = ["excited to announce", "hiring for", "new role", "personal news"]
    if any(n in text_lower for n in noise):
        return False, 0

    # Signal Score: Looking for technical depth
    signals = {
        'inference': 3, 'weights': 3, 'parameters': 3, 'latency': 2, 
        'benchmark': 2, 'transformer': 2, 'dataset': 2, 'gpu': 1,
        'token': 1, 'open-source': 1, 'architecture': 1, 'training': 1
    }
    
    score = sum(points for word, points in signals.items() if word in text_lower)
    return (score >= 4), score

def fetch_wide_ai_news():
    print("🌍 Searching the global web for AI news...")
    # GNews search query for "AI Research" or "AI News"
    url = f"https://gnews.io/api/v4/search?q=\"artificial intelligence\" OR \"AI research\"&lang=en&max=50&apikey={GNEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        articles_raw = response.json().get('articles', [])
        valid_articles = []
        
        for entry in articles_raw:
            story_url = entry.get('url')
            domain = story_url.split('/')[2].replace('www.', '')
            
            # Use Newspaper3k to "read" the article
            article = Article(story_url, config=config)
            try:
                article.download()
                article.parse()
                
                is_quality, score = evaluate_content_quality(article.text, domain)
                
                if is_quality:
                    # Clean for HTML
                    clean_content = article.text[:1000].replace('\n', '<br>')
                    valid_articles.append({
                        'title': entry['title'],
                        'url': story_url,
                        'author': entry['source']['name'],
                        'source': domain,
                        'content': clean_content,
                        'score': score
                    })
                    print(f"    [PICKED - Score {score}]: {entry['title']}")
            except:
                continue
            
            # Sort by score and take top 5
            valid_articles = sorted(valid_articles, key=lambda x: x['score'], reverse=True)
            if len(valid_articles) >= 7: break 
            
        return valid_articles[:5]
    except Exception as e:
        print(f"Error: {e}")
        return []

# ... [Include ArXiv and Publish functions from previous script] ...

if __name__ == "__main__":
    # If GNEWS_API_KEY is in environment variables (GitHub Secrets)
    GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', 'your_backup_key_here')
    
    news = fetch_wide_ai_news()
    papers = fetch_arxiv_papers()
    publish_gazette(news, papers)
