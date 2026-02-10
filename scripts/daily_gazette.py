import requests
import os
import datetime
from bs4 import BeautifulSoup
import time

# 1. SETUP
API_KEY = os.environ.get("NEWS_API_KEY")

# 2. HELPER: SCRAPE FULL TEXT
def get_full_article_text(url):
    """
    Visits the external news link and tries to grab the paragraph text
    so the user can read it without leaving the site.
    """
    print(f"   ...Attempting to scrape: {url[:50]}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # specific logic for common tech sites could go here, 
        # but we will use a generic "grab all <p>" approach
        paragraphs = soup.find_all('p')
        
        # Filter out short "menu" or "footer" text
        text_content = ""
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 60: # Only keep substantial paragraphs
                text_content += f"<p>{text}</p>"
        
        if len(text_content) < 500: # If we failed to get much text
            return None
            
        return text_content
    except:
        return None # Fallback to default description if scraping fails

# 3. FETCH NEWS (AI ONLY)
def fetch_news():
    if not API_KEY:
        print("❌ No API Key found!")
        return []
    
    print("🗞️ Fetching AI Headlines...")
    # Strict Query: AI must be in the title or body, sorted by relevance/date
    url = f"https://newsapi.org/v2/everything?q=artificial+intelligence&language=en&sortBy=publishedAt&apiKey={API_KEY}"
    
    try:
        data = requests.get(url).json()
        raw_articles = data.get("articles", [])
        
        # Process the top 3 articles to get full text
        processed_articles = []
        for art in raw_articles[:3]: 
            full_text = get_full_article_text(art['url'])
            
            # If we couldn't scrape it, use the description provided by API
            if full_text:
                art['content'] = full_text
                art['is_scraped'] = True
            else:
                art['content'] = f"<p>{art['description']}</p><p><i>(Full content protected. Click source to read more.)</i></p>"
                art['is_scraped'] = False
                
            processed_articles.append(art)
            time.sleep(1) # Be polite to servers
            
        return processed_articles
    except Exception as e:
        print(f"Error: {e}")
        return []

# 4. FETCH PAPERS (WITH LINKS)
def fetch_papers():
    print("🔬 Fetching ArXiv Papers (AI + NLP)...")
    
    # query: (category: AI OR category: Computation & Language)
    # sortBy: submittedDate (get the freshest preprints)
    url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL&start=0&max_results=6&sortBy=submittedDate&sortOrder=descending"
    
    try:
        response = requests.get(url)
        entries = response.text.split('<entry>')
        papers = []
        
        # Skip the first entry because it is metadata, not a paper
        for entry in entries[1:]:
            # Extract Link
            try:
                link = entry.split('<id>')[1].split('</id>')[0].strip()
            except:
                link = "#"
            
            # Extract Title
            try:
                title = entry.split('<title>')[1].split('</title>')[0].strip()
                # Clean up newlines in titles
                title = title.replace('\n', ' ')
            except:
                title = "Unknown Title"
            
            # Extract Summary
            try:
                summary = entry.split('<summary>')[1].split('</summary>')[0].strip()
                # Clean up newlines in summaries
                summary = summary.replace('\n', ' ')
            except:
                summary = "No summary available."
            
            # Extract Category to show the user (e.g., "CS.CL")
            # This is a bit tricky with XML splitting, but we can just label them "Preprint"
            # or try to find the primary category tag if we want to be fancy.
            # For now, we will stick to the basics.

            papers.append({'title': title, 'summary': summary, 'link': link})
            
        return papers
    except Exception as e:
        print(f"Error fetching papers: {e}")
        return []

# 5. GENERATE HTML
def generate_html(articles, papers):
    if not articles:
        articles = [{"title": "No News Found", "author": "System", "content": "<p>Check API Key.</p>", "url": "#", "publishedAt": datetime.datetime.now().isoformat()}]
    
    main_story = articles[0]
    side_stories = articles[1:]
    today = datetime.datetime.now().strftime("%A, %B %d, %Y").upper()

    # --- HTML COMPONENTS ---
    
    # Side Stories HTML
    sidebar_html = ""
    for story in side_stories:
        sidebar_html += f"""
        <div class="side-article">
            <h4>{story['title']}</h4>
            <span class="meta-tag">{story['source']['name']}</span>
            <div class="article-body">{story['content'][:400]}...</div>
            <a href="{story['url']}" target="_blank" class="read-link">Read Original Source</a>
        </div>
        """

    # Papers HTML (Now with Links!)
    papers_html = ""
    for paper in papers:
        papers_html += f"""
        <article class="paper">
            <span class="paper-tag">CS.AI Research</span>
            <h4><a href="{paper['link']}" target="_blank">{paper['title']}</a></h4>
            <p>{paper['summary'][:250]}...</p>
            <a href="{paper['link']}" target="_blank" class="read-link">View on ArXiv &rarr;</a>
        </article>
        """

    # Full Page HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>The Gemini Gazette | AI Edition</title>
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Merriweather:ital,wght@0,300;0,400;0,700;1,300&display=swap" rel="stylesheet">
        <style>
            :root {{ --paper: #fdf6e3; --ink: #2c2c2c; --accent: #8b0000; }}
            body {{ background: #e0e0e0; font-family: 'Merriweather', serif; color: var(--ink); margin: 0; padding: 20px; }}
            a {{ color: var(--accent); text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            
            /* Newspaper Layout */
            .container {{ max-width: 1100px; margin: 0 auto; background: var(--paper); padding: 40px; box-shadow: 0 0 20px rgba(0,0,0,0.3); border: 1px solid #d4cbb8; }}
            
            /* Header */
            header {{ text-align: center; border-bottom: 4px double var(--ink); margin-bottom: 30px; padding-bottom: 10px; }}
            h1 {{ font-family: 'Playfair Display', serif; font-size: 5rem; margin: 10px 0; text-transform: uppercase; line-height: 0.9; }}
            .sub-header {{ display: flex; justify-content: space-between; border-top: 2px solid var(--ink); border-bottom: 1px solid var(--ink); padding: 8px 0; font-family: sans-serif; font-size: 0.8rem; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }}

            /* Grid Layout */
            .main-content {{ display: grid; grid-template-columns: 2fr 1fr; gap: 40px; }}
            
            /* Main Story */
            .hero-article h2 {{ font-family: 'Playfair Display', serif; font-size: 3rem; margin: 0 0 15px 0; line-height: 1; }}
            .hero-article .meta {{ font-style: italic; color: #555; display: block; margin-bottom: 20px; }}
            .dropcap::first-letter {{ font-family: 'Playfair Display', serif; font-size: 4.5rem; float: left; line-height: 0.8; padding-right: 12px; font-weight: 700; color: var(--accent); }}
            .article-body p {{ line-height: 1.6; margin-bottom: 15px; text-align: justify; }}

            /* Sidebar */
            .sidebar {{ border-left: 1px solid #ccc; padding-left: 30px; }}
            .sidebar h3 {{ font-family: sans-serif; text-transform: uppercase; border-bottom: 3px solid var(--ink); font-size: 1.1rem; margin-bottom: 20px; }}
            
            /* Components */
            .side-article {{ margin-bottom: 30px; border-bottom: 1px dotted #999; padding-bottom: 20px; }}
            .side-article h4 {{ font-family: 'Playfair Display', serif; font-size: 1.5rem; margin: 0 0 5px 0; }}
            .paper {{ margin-bottom: 25px; background: rgba(0,0,0,0.03); padding: 15px; border-radius: 4px; }}
            .paper h4 {{ margin: 5px 0; font-family: 'Playfair Display', serif; font-size: 1.2rem; }}
            .paper-tag {{ font-family: sans-serif; font-size: 0.6rem; background: var(--ink); color: #fff; padding: 2px 6px; text-transform: uppercase; }}
            
            .read-link {{ font-family: sans-serif; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; display: inline-block; margin-top: 10px; }}

            /* Mobile */
            @media (max-width: 800px) {{ .main-content {{ grid-template-columns: 1fr; }} .sidebar {{ border-left: none; border-top: 4px double var(--ink); padding-left: 0; padding-top: 30px; margin-top: 30px; }} h1 {{ font-size: 3rem; }} }}
        </style>
    </head>
    <body>
    <div class="container">
        <header>
            <div class="sub-header">
                <span>Vol. 1</span>
                <span>{today}</span>
                <span>FREE EDITION</span>
            </div>
            <h1>The Gemini Gazette</h1>
            <div class="sub-header" style="border-bottom: none; border-top: 1px solid black;">
                <span>AI Special Edition</span>
                <span>"Read All About It"</span>
                <span>Status: GENERATED</span>
            </div>
        </header>

        <main class="main-content">
            <section>
                <article class="hero-article">
                    <h2>{main_story['title']}</h2>
                    <span class="meta">By {main_story.get('author') or 'Editorial Staff'} • {main_story['source']['name']}</span>
                    
                    <div class="article-body dropcap">
                        {main_story['content']}
                    </div>
                </article>

                <br><br>
                <div style="border-top: 4px double var(--ink); padding-top: 20px;">
                    <h3 style="font-family: sans-serif; text-transform: uppercase;">Latest Research Papers</h3>
                    {papers_html}
                </div>
            </section>

            <aside class="sidebar">
                <h3>More Headlines</h3>
                {sidebar_html}
                
                <div style="background: var(--ink); color: #fff; padding: 20px; text-align: center; margin-top: 40px;">
                    <p style="font-family: sans-serif; text-transform: uppercase; font-weight: bold; margin-bottom: 5px;">Weather</p>
                    <p style="font-size: 2rem; margin: 0; font-family: 'Playfair Display', serif;">72°F</p>
                    <p>Sunny in the Server Room</p>
                </div>
            </aside>
        </main>
    </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ index.html generated successfully")

if __name__ == "__main__":
    news = fetch_news()
    papers = fetch_papers()
    generate_html(news, papers)
