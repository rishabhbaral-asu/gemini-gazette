```python
import requests
import datetime
from bs4 import BeautifulSoup


# ============================================================
# TOPIC DEFINITIONS
# ============================================================

TOPIC_KEYWORDS = {
    "HEALTHCARE & AGENTIC AI": {
        "healthcare": [
            "healthcare",
            "health care",
            "clinical",
            "medical",
            "medicine",
            "patient",
            "physician",
            "doctor",
            "hospital",
            "diagnosis",
            "diagnostic",
            "electronic health record",
            "ehr",
            "biomedical",
            "medagent",
            "medical agent",
            "clinical agent",
        ],
        "agentic": [
            "agent",
            "agents",
            "agentic",
            "autonomous agent",
            "generative agent",
            "multi-agent",
            "tool use",
            "tool-using",
            "tool calling",
            "workflow",
            "planning",
            "decision making",
            "decision-making",
        ],
    },

    "CYBERSECURITY": [
        "cybersecurity",
        "cyber security",
        "computer security",
        "security agent",
        "security agents",
        "vulnerability",
        "vulnerabilities",
        "exploit",
        "exploitation",
        "malware",
        "ransomware",
        "phishing",
        "intrusion",
        "cyber attack",
        "cyberattack",
        "adversarial attack",
        "penetration testing",
        "pentesting",
        "red teaming",
        "red team",
        "prompt injection",
        "jailbreak",
        "jailbreaking",
        "data poisoning",
        "backdoor",
        "software security",
        "network security",
        "authentication",
        "authorization",
        "access control",
    ],

    "POLICY FOLLOWING": [
        "policy following",
        "policy adherence",
        "policy compliance",
        "instruction following",
        "instruction hierarchy",
        "instruction adherence",
        "constraint following",
        "constraint satisfaction",
        "rule following",
        "rule adherence",
        "behavioral policy",
        "safety policy",
        "system prompt",
        "system instruction",
        "prompt injection",
        "jailbreak",
        "jailbreaking",
        "alignment",
        "aligned behavior",
        "refusal",
        "safety alignment",
    ],
}


# ============================================================
# TOPIC CLASSIFICATION
# ============================================================

def contains_keyword(text, keywords):
    """
    Returns True if any keyword appears in the supplied text.
    """
    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)


def classify_topics(title, summary):
    """
    Classifies a paper into the three NEW topical desks.

    Papers can appear in multiple topical desks.

    Healthcare & Agentic AI intentionally requires BOTH:
        1. a healthcare signal
        2. an agentic/decision-making signal

    This prevents generic medical imaging / biomedical papers
    from flooding the Healthcare & Agentic AI desk.
    """
    text = f"{title} {summary}".lower()
    topics = []

    # --------------------------------------------------------
    # Healthcare & Agentic AI
    # --------------------------------------------------------

    healthcare_terms = TOPIC_KEYWORDS[
        "HEALTHCARE & AGENTIC AI"
    ]["healthcare"]

    agentic_terms = TOPIC_KEYWORDS[
        "HEALTHCARE & AGENTIC AI"
    ]["agentic"]

    if (
        contains_keyword(text, healthcare_terms)
        and contains_keyword(text, agentic_terms)
    ):
        topics.append("HEALTHCARE & AGENTIC AI")

    # --------------------------------------------------------
    # Cybersecurity
    # --------------------------------------------------------

    if contains_keyword(
        text,
        TOPIC_KEYWORDS["CYBERSECURITY"]
    ):
        topics.append("CYBERSECURITY")

    # --------------------------------------------------------
    # Policy Following
    # --------------------------------------------------------

    if contains_keyword(
        text,
        TOPIC_KEYWORDS["POLICY FOLLOWING"]
    ):
        topics.append("POLICY FOLLOWING")

    return topics


# ============================================================
# PRIORITY SCORING
# ============================================================

def calculate_priority(title, summary):
    """
    Assigns a score to papers based on topics of interest.

    Higher score = more relevant to:
        - Agents
        - World Models
        - Reasoning
        - Planning
        - Reinforcement Learning
        - Healthcare Agents
        - Cybersecurity
        - Policy Following
    """

    text = (title + " " + summary).lower()
    score = 0

    # --------------------------------------------------------
    # Tier 1: Agents & World Models
    # --------------------------------------------------------

    high_priority = [
        "world model",
        "autonomous agent",
        "generative agent",
        "agentic",
        "multi-agent",
    ]

    if any(k in text for k in high_priority):
        score += 10

    # --------------------------------------------------------
    # Tier 2: Reasoning / Planning / RL
    # --------------------------------------------------------

    medium_priority = [
        "reasoning",
        "planning",
        "chain of thought",
        "chain-of-thought",
        "reinforcement learning",
        "policy",
    ]

    if any(k in text for k in medium_priority):
        score += 5

    # --------------------------------------------------------
    # Healthcare + Agentic AI
    # --------------------------------------------------------

    healthcare_terms = TOPIC_KEYWORDS[
        "HEALTHCARE & AGENTIC AI"
    ]["healthcare"]

    agentic_terms = TOPIC_KEYWORDS[
        "HEALTHCARE & AGENTIC AI"
    ]["agentic"]

    if (
        contains_keyword(text, healthcare_terms)
        and contains_keyword(text, agentic_terms)
    ):
        score += 8

    # --------------------------------------------------------
    # Cybersecurity
    # --------------------------------------------------------

    strong_security_signals = [
        "cybersecurity",
        "cyber security",
        "prompt injection",
        "jailbreak",
        "jailbreaking",
        "vulnerability",
        "malware",
        "ransomware",
        "red teaming",
        "red team",
        "penetration testing",
        "security agent",
    ]

    if contains_keyword(text, strong_security_signals):
        score += 7

    # --------------------------------------------------------
    # Policy Following
    # --------------------------------------------------------

    strong_policy_signals = [
        "policy following",
        "policy adherence",
        "policy compliance",
        "instruction hierarchy",
        "instruction following",
        "instruction adherence",
        "constraint following",
        "rule following",
        "safety policy",
    ]

    if contains_keyword(text, strong_policy_signals):
        score += 8

    return score


# ============================================================
# FETCH ARXIV RESEARCH
# ============================================================

def fetch_arxiv_research():

    # --------------------------------------------------------
    # 1. DATE CALCULATION
    # --------------------------------------------------------

    # ArXiv timestamps are UTC.
    today = datetime.datetime.now(datetime.timezone.utc)
    seven_days_ago = today - datetime.timedelta(days=7)

    print(
        "🔬 Fetching recent papers and filtering "
        "for the last 7 days..."
    )

    # --------------------------------------------------------
    # 2. QUERY CONSTRUCTION
    # --------------------------------------------------------

    # Original categories:
    #   cs.AI
    #   cs.CL
    #   cs.CV
    #
    # Additional categories are included so the new desks
    # don't miss papers that naturally appear elsewhere.

    categories = [
        "cat:cs.AI",     # Artificial Intelligence
        "cat:cs.CL",     # Computation and Language
        "cat:cs.CV",     # Computer Vision
        "cat:cs.LG",     # Machine Learning
        "cat:cs.CR",     # Cryptography and Security
        "cat:cs.CY",     # Computers and Society
        "cat:cs.HC",     # Human-Computer Interaction
        "cat:q-bio.QM",  # Quantitative Methods / biomedical
    ]

    base_query = "+OR+".join(categories)

    url = (
        "https://export.arxiv.org/api/query?"
        f"search_query={base_query}"
        "&sortBy=submittedDate"
        "&sortOrder=descending"
        "&max_results=1000"
    )

    headers = {
        "User-Agent": (
            "SiliconScroll/1.0 "
            "(weekly research discovery tool)"
        )
    }

    # --------------------------------------------------------
    # ORIGINAL + NEW DESKS
    # --------------------------------------------------------

    sections = {
        # Original desks
        "AI & REINFORCEMENT": [],
        "NLP & LANGUAGE": [],
        "VISION & MULTIMODAL": [],

        # New desks
        "HEALTHCARE & AGENTIC AI": [],
        "CYBERSECURITY": [],
        "POLICY FOLLOWING": [],
    }

    try:

        res = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        res.raise_for_status()

        soup = BeautifulSoup(
            res.content,
            "xml"
        )

        entries = soup.find_all("entry")

        print(
            f"   ↳ Fetched {len(entries)} papers from ArXiv. "
            "Filtering by date and priority..."
        )

        # ----------------------------------------------------
        # PROCESS PAPERS
        # ----------------------------------------------------

        for entry in entries:

            # Parse exact ArXiv publication date.
            published_str = entry.published.text

            published_date = datetime.datetime.strptime(
                published_str,
                "%Y-%m-%dT%H:%M:%SZ"
            ).replace(
                tzinfo=datetime.timezone.utc
            )

            # Ignore anything older than seven days.
            if published_date < seven_days_ago:
                continue

            # ------------------------------------------------
            # PRIMARY CATEGORY
            # ------------------------------------------------

            primary_category = entry.find(
                "arxiv:primary_category"
            )

            if primary_category:
                primary_cat = primary_category["term"]
            else:
                primary_cat = ""

            # ------------------------------------------------
            # TITLE / SUMMARY
            # ------------------------------------------------

            title = (
                entry.title.text
                .strip()
                .replace("\n", " ")
            )

            summary = (
                entry.summary.text
                .strip()
                .replace("\n", " ")
            )

            # ------------------------------------------------
            # AUTHORS
            # ------------------------------------------------

            authors = [
                author.find("name").text
                for author in entry.find_all("author")
            ]

            # Keep first two authors for display.
            display_authors = authors[:2]

            # ------------------------------------------------
            # PAPER OBJECT
            # ------------------------------------------------

            paper = {
                "title": title,
                "summary": summary,
                "link": entry.id.text.strip(),
                "authors": display_authors,
                "date": published_date.strftime(
                    "%Y-%m-%d"
                ),
                "priority_score": calculate_priority(
                    title,
                    summary
                ),
                "primary_category": primary_cat,
            }

            # =================================================
            # ORIGINAL DESK LOGIC
            # =================================================
            #
            # This intentionally preserves the behavior of your
            # original Silicon Scroll.
            #
            # cs.CL -> NLP
            # cs.CV -> Vision
            # everything else -> AI & Reinforcement
            #
            # =================================================

            if primary_cat == "cs.CL":

                sections[
                    "NLP & LANGUAGE"
                ].append(paper)

            elif primary_cat == "cs.CV":

                sections[
                    "VISION & MULTIMODAL"
                ].append(paper)

            else:

                sections[
                    "AI & REINFORCEMENT"
                ].append(paper)

            # =================================================
            # NEW TOPICAL DESKS
            # =================================================
            #
            # These are ADDITIVE.
            #
            # A paper can therefore appear in:
            #
            #   NLP & LANGUAGE
            #
            # AND
            #
            #   POLICY FOLLOWING
            #
            # for example.
            #
            # =================================================

            topics = classify_topics(
                title,
                summary
            )

            for topic in topics:
                sections[topic].append(paper)

        # ----------------------------------------------------
        # SORT EACH DESK
        # ----------------------------------------------------

        for key in sections:

            sections[key].sort(
                key=lambda x: (
                    x["priority_score"],
                    x["date"]
                ),
                reverse=True
            )

        # ----------------------------------------------------
        # CONSOLE SUMMARY
        # ----------------------------------------------------

        print("\n📰 THE SILICON SCROLL — DESK SUMMARY")

        for name, papers in sections.items():

            print(
                f"   {name}: {len(papers)} papers"
            )

        print()

        return sections

    except Exception as e:

        print(f"❌ Error fetching ArXiv: {e}")

        return {}


# ============================================================
# HTML GENERATION
# ============================================================

def publish_sectioned_gazette(sections):

    today = datetime.datetime.now().strftime(
        "%B %d, %Y"
    ).upper()

    sections_html = ""

    # --------------------------------------------------------
    # DESK COLORS
    # --------------------------------------------------------

    accent_map = {
        "AI & REINFORCEMENT": "ai-accent",
        "NLP & LANGUAGE": "nlp-accent",
        "VISION & MULTIMODAL": "vision-accent",
        "HEALTHCARE & AGENTIC AI": "health-accent",
        "CYBERSECURITY": "cyber-accent",
        "POLICY FOLLOWING": "policy-accent",
    }

    # --------------------------------------------------------
    # DESK ICONS
    # --------------------------------------------------------

    icon_map = {
        "AI & REINFORCEMENT": "🤖",
        "NLP & LANGUAGE": "💬",
        "VISION & MULTIMODAL": "👁️",
        "HEALTHCARE & AGENTIC AI": "⚕️",
        "CYBERSECURITY": "🛡️",
        "POLICY FOLLOWING": "📜",
    }

    # --------------------------------------------------------
    # GENERATE EACH DESK
    # --------------------------------------------------------

    for name, papers in sections.items():

        if not papers:
            continue

        paper_cards = ""

        # Maximum 30 visible papers per desk.
        for p in papers[:30]:

            accent = accent_map.get(
                name,
                ""
            )

            # ------------------------------------------------
            # PRIORITY ICON
            # ------------------------------------------------

            if p["priority_score"] >= 15:

                priority_icon = "🔥 "

            elif p["priority_score"] >= 5:

                priority_icon = "⚡ "

            else:

                priority_icon = ""

            # ------------------------------------------------
            # AUTHORS
            # ------------------------------------------------

            author_text = ", ".join(
                p["authors"]
            )

            # ------------------------------------------------
            # CARD
            # ------------------------------------------------

            paper_cards += f"""
            <div class="card {accent}">

                <div class="card-date">
                    {p['date']}
                    &nbsp;•&nbsp;
                    {p['primary_category']}
                </div>

                <h3>
                    <a
                        href="{p['link']}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        {priority_icon}{p['title']}
                    </a>
                </h3>

                <p class="meta">
                    By {author_text}
                </p>

                <p class="text">
                    {p['summary'][:280]}...
                </p>

            </div>
            """

        desk_icon = icon_map.get(
            name,
            ""
        )

        sections_html += f"""
        <section class="news-desk">

            <h2 class="desk-title">

                <div>
                    {desk_icon} {name} DESK
                </div>

                <span>
                    {len(papers)} PAPERS THIS WEEK
                </span>

            </h2>

            <div class="horizontal-scroll">
                {paper_cards}
            </div>

        </section>
        """

    # ========================================================
    # PAGE
    # ========================================================

    html = f"""
    <!DOCTYPE html>

    <html lang="en">

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>
            The Silicon Scroll | Weekly Research
        </title>

        <style>

            @import url(
                'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=Libre+Baskerville:wght@400;700&display=swap'
            );

            * {{
                box-sizing: border-box;
            }}

            body {{
                background: #f4f1ea;
                color: #1a1a1a;
                font-family: 'Libre Baskerville', serif;
                margin: 0;
                padding: 2vw;
            }}

            /* ==============================================
               MASTHEAD
               ============================================== */

            .masthead {{
                text-align: center;
                border-bottom: 5px double #333;
                margin-bottom: 40px;
                padding-bottom: 15px;
            }}

            .masthead h1 {{
                font-family: 'Playfair Display', serif;
                font-size: clamp(3rem, 7vw, 5rem);
                margin: 0;
                letter-spacing: -2px;
            }}

            .masthead p {{
                font-size: 0.8rem;
                letter-spacing: 1px;
            }}

            /* ==============================================
               NEWS DESKS
               ============================================== */

            .news-desk {{
                margin-bottom: 50px;
            }}

            .desk-title {{
                border-bottom: 2px solid #333;
                font-family: 'Playfair Display', serif;
                font-size: 1.8rem;
                margin-bottom: 15px;
                padding-bottom: 5px;

                display: flex;
                justify-content: space-between;
                align-items: center;

                gap: 20px;
            }}

            .desk-title span {{
                font-size: 0.7rem;
                font-family: 'Libre Baskerville', serif;
                opacity: 0.5;
                white-space: nowrap;
            }}

            /* ==============================================
               HORIZONTAL SCROLL
               ============================================== */

            .horizontal-scroll {{
                display: flex;
                overflow-x: auto;
                gap: 25px;
                padding: 5px 3px 20px 3px;

                scrollbar-width: thin;
                scrollbar-color: #333 #f4f1ea;
            }}

            .horizontal-scroll::-webkit-scrollbar {{
                height: 8px;
            }}

            .horizontal-scroll::-webkit-scrollbar-track {{
                background: #f4f1ea;
            }}

            .horizontal-scroll::-webkit-scrollbar-thumb {{
                background: #333;
                border-radius: 4px;
            }}

            /* ==============================================
               PAPER CARDS
               ============================================== */

            .card {{
                flex: 0 0 350px;

                background: #fffefc;

                border: 1px solid #d1cec1;

                padding: 25px;

                box-shadow:
                    4px 4px 0 rgba(0, 0, 0, 0.05);

                transition:
                    transform 0.2s ease,
                    box-shadow 0.2s ease;

                display: flex;
                flex-direction: column;
            }}

            .card:hover {{
                transform: translateY(-5px);

                box-shadow:
                    6px 8px 0 rgba(0, 0, 0, 0.08);
            }}

            .card-date {{
                font-size: 10px;
                font-weight: bold;
                color: #777;
                margin-bottom: 10px;
            }}

            h3 {{
                font-family: 'Playfair Display', serif;
                font-size: 1.3rem;
                margin: 0 0 10px 0;
                line-height: 1.2;
            }}

            h3 a {{
                color: #1a1a1a;
                text-decoration: none;
            }}

            h3 a:hover {{
                text-decoration: underline;
            }}

            .meta {{
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
                color: #555;
                margin-bottom: 10px;
            }}

            .text {{
                font-size: 13px;
                line-height: 1.6;
                color: #333;
                flex-grow: 1;
            }}

            /* ==============================================
               ORIGINAL DESK COLORS
               ============================================== */

            .ai-accent {{
                border-top: 6px solid #2c3e50;
            }}

            .nlp-accent {{
                border-top: 6px solid #27ae60;
            }}

            .vision-accent {{
                border-top: 6px solid #e67e22;
            }}

            /* ==============================================
               NEW DESK COLORS
               ============================================== */

            .health-accent {{
                border-top: 6px solid #c0392b;
            }}

            .cyber-accent {{
                border-top: 6px solid #6c3483;
            }}

            .policy-accent {{
                border-top: 6px solid #2471a3;
            }}

            /* ==============================================
               MOBILE
               ============================================== */

            @media (max-width: 700px) {{

                body {{
                    padding: 18px;
                }}

                .desk-title {{
                    align-items: flex-start;
                    flex-direction: column;
                    gap: 4px;
                }}

                .card {{
                    flex-basis: 85vw;
                }}

            }}

        </style>

    </head>

    <body>

        <header class="masthead">

            <div
                style="
                    font-size: 50px;
                    margin-bottom: 10px;
                "
            >
                🦉
            </div>

            <h1>
                The Silicon Scroll
            </h1>

            <p>
                TEMPE, AZ
                —
                {today}
                —
                WEEKLY INTELLIGENCE
            </p>

        </header>

        <main>

            {sections_html}

        </main>

    </body>

    </html>
    """

    # --------------------------------------------------------
    # WRITE FILE
    # --------------------------------------------------------

    with open(
        "index.html",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)

    print(
        "✅ Gazette published: "
        "The Silicon Scroll is ready."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    data = fetch_arxiv_research()

    publish_sectioned_gazette(data)
```
