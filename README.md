# Media Recommendations

A personal media tracking and recommendation app powered by Claude. Chat naturally to track movies, games, music, books, or any other media — along with your ratings — and get personalized recommendations based on what you've enjoyed.

## Features

- **Chat interface** — add and manage media through natural conversation
- **Media types** — create custom categories (Movies, Games, Music, Books, etc.)
- **Ratings** — rate media 0–5, or mark items as not yet seen/played
- **Genres** — tag items by genre and filter recommendations (e.g. "recommend me a horror movie")
- **Recommendations** — Claude references your rated media to suggest what to watch or play next
- **Media sidebar** — browse your full library at a glance, organized by type

## Prerequisites

- Python 3.8 or newer
- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)

## Setup

**1. Clone or download this repository**

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure your API key**

Copy the example environment file and add your key:

```bash
cp .env.example .env
```

Open `.env` and replace `your-api-key-here` with your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

**4. Start the server**

```bash
python -m uvicorn main:app --reload
```

**5. Open the app**

Navigate to [http://localhost:8000](http://localhost:8000) in your browser.

## Usage Examples

| What you want to do | What to say |
|---|---|
| Add a media type | "Add Movies and Games as media types" |
| Track something you watched | "I watched Inception, 5 out of 5, it's a thriller" |
| Add something to watch later | "Add Dune Part Two to Movies, haven't seen it yet" |
| Rate something you already added | "Update my Elden Ring rating to 4.5" |
| Get recommendations | "Recommend me some horror movies" |
| Browse your library | "Show me everything in my Games list" |
| Remove an item | "Remove Inception from Movies" |

## Project Structure

```
media_recommendations/
├── main.py          # FastAPI server and Claude agent
├── database.py      # SQLite database setup and queries
├── static/
│   └── index.html   # Chat UI and media sidebar
├── requirements.txt
├── .env             # Your API key (not committed)
└── .env.example     # Template for API key setup
```

## Notes

- Your media library is stored locally in `media.db` — no data is sent anywhere except your chat messages to the Anthropic API.
- The assistant is restricted to media tracking and recommendations. It will decline off-topic requests.
- Each person running the app uses their own API key and gets their own local database.
