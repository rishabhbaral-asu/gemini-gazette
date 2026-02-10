import requests
import os
import datetime

# 1. GET API KEY FROM GITHUB SECRETS
# (We will set this up in the repo settings later)
API_KEY = '02cd196b860e4d3e83a0535aa25569b3'

def fetch_news():
    if not API_KEY:
        return []
    print("🗞️ Fetching News...")
    url = f"https://newsapi.org/v2/everything?q=artificial+intelligence&language=en&sortBy=publishedAt&apiKey={API_KEY}"
    try:
        data = requests.get(url).json()
        return data.get("articles", [])[:5] # Get top 5
    except:
        return []

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

def generate_html(articles, papers):
    # Fallback if API fails
    if not articles:
        articles = [{"title": "News Feed Currently Quiet", "author": "System", "description": "Check back later.", "url": "#", "publishedAt": datetime.datetime.now().isoformat()}]
    
    main_story = articles[0]
    side_stories = articles[1:]
    
    today = datetime.datetime.now().strftime("%A, %B %d, %Y").upper()

    # Generate Sidebar HTML
    sidebar_html = ""
    for story in side_stories:
        sidebar_html += f"""
        <div style="margin-bottom: 15px; border-bottom: 1px dotted #ccc; padding-bottom: 5px;">
            <a href="{story['url']}" target="_blank" style="text-decoration: none; color: inherit; font-weight: bold; font-family: 'Playfair Display', serif;">
                {story['title']}
            </a>
            <div style="font-size: 0.7rem; color: #888; margin-top:2px;">{story['source']['name']}</div>
        </div>
        """

    # Generate Papers HTML
    papers_html = ""
    for paper in papers:
        papers_html += f"""
        <article style="margin-bottom: 15px; border-bottom: 1px solid #e0e0e0; padding-bottom: 10px;">
            <span class="paper-tag" style="background: #333; color: #fff; padding: 2px 6px; font-size: 0.6rem;">CS.AI</span>
            <h4 style="margin: 5px 0;">{paper['title']}</h4>
            <p style="font-size: 0.9rem;">{paper['summary']}</p>
        </article>
        """

    # The HTML Template
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>The Gemini Gazette</title>
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Merriweather:ital,wght@0,300;0,400;0,700;1,300&display=swap" rel="stylesheet">
        <style>
            :root {{ --paper: #fdf6e3; --ink: #2c2c2c; }}
            body {{ background: #dedede; font-family: 'Merriweather', serif; color: var(--ink); margin: 0; padding: 20px; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: var(--paper); padding: 30px 50px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); border: 1px solid #d4cbb8; }}
            header {{ text-align: center; border-bottom: 3px double var(--ink); margin-bottom: 25px; }}
            h1 {{ font-family: 'Playfair Display', serif; font-size: 4rem; margin: 10px 0; text-transform: uppercase; line-height: 1; }}
            .meta {{ display: flex; justify-content: space-between; border-top: 2px solid var(--ink); border-bottom: 1px solid var(--ink); padding: 5px 0; font-family: sans-serif; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }}
            .grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 40px; }}
            h2 {{ font-family: 'Playfair Display', serif; font-size: 2.2rem; margin: 0 0 10px 0; line-height: 1.1; }}
            .dropcap::first-letter {{ font-family: 'Playfair Display', serif; font-size: 3.5rem; float: left; line-height: 0.8; padding-right: 8px; font-weight: 700; }}
            @media (max-width: 700px) {{ .grid {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
    <div class="container">
        <header>
            <div class="meta"><span>Vol. 1</span><span>{today}</span><span>GitHub Actions Edition</span></div>
            <h1>The Gemini Gazette</h1>
            <div class="meta" style="border-bottom: none; border-top: 1px solid black;"><span>Global Edition</span><span>"Live Intelligence"</span><span>Status: ONLINE</span></div>
        </header>
        <div class="grid">
            <section>
                <article>
                    <h2>{main_story['title']}</h2>
                    <span style="font-style:italic; color:#666;">By {main_story.get('author') or 'Staff'}</span>
                    <p class="dropcap">{main_story.get('description') or 'Click read more...'}</p>
                    <p><a href="{main_story['url']}" target="_blank">Read Full Story &rarr;</a></p>
                </article>
                <hr style="margin: 30px 0; border: 0; border-top: 1px solid #333;">
                <h3>Latest Papers</h3>
                {papers_html}
            </section>
            <aside style="border-left: 1px solid #ccc; padding-left: 20px;">
                <h3 style="font-family:sans-serif; text-transform:uppercase; border-bottom:2px solid black;">Headlines</h3>
                {sidebar_html}
                <br>
                <h3 style="font-family:sans-serif; text-transform:uppercase; border-bottom:2px solid black;">Market</h3>
                <p><b>NVIDIA:</b> ▲ Bullish<br><b>OPENAI:</b> ▲ Shipping</p>
            </aside>
        </div>
    </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ index.html generated successfully")

if __name__ == "__main__":
    articles = fetch_news()
    papers = fetch_papers()
    generate_html(articles, papers)
