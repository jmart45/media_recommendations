# Media Recommendations

A personal media tracking and recommendation app with an AI chat interface. Talk naturally to track movies, games, music, books, or any other media — with ratings and genres — and get personalized recommendations based on what you've enjoyed.

Supports **Google Gemini 3.5 Flash** and **Groq (Llama 3.3 70B)** as LLM providers. Both have free tiers. Switch between them with a single `.env` setting.

## Features

- **Chat interface** — add and manage media through natural conversation
- **Custom media types** — create categories like Movies, Games, Music, Books, etc.
- **Ratings** — rate items 0–5, or mark them as not yet seen/played
- **Genres** — tag items by genre; filter recommendations by genre
- **Recommendations** — the agent references your rated media to suggest what to try next
- **Sidebar** — browse your full library at a glance, organized by type, with inline genre editing
- **Browse page** — sortable, filterable table with posters, descriptions, and ratings from [TMDB](https://www.themoviedb.org/) (optional)

## Prerequisites

- Python 3.12+
- Node.js 20+
- A free API key for at least one LLM provider:
  - **Gemini** — [aistudio.google.com](https://aistudio.google.com) (default)
  - **Groq** — [console.groq.com](https://console.groq.com)

## Setup

**1. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**2. Configure environment**

Create a `.env` file in the project root:

```
LLM_PROVIDER=gemini        # or: groq
GEMINI_API_KEY=...
GROQ_API_KEY=...
TMDB_API_KEY=...           # optional — enables posters and metadata on Browse page
```

`LLM_PROVIDER` defaults to `gemini` if omitted. Only the key for your chosen provider is required.

Get a free TMDB key at [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api).

**3. Install frontend dependencies**

```bash
cd frontend && npm install && cd ..
```

**4. Start the app**

```bash
python start.py
```

Opens the API on [http://localhost:8000](http://localhost:8000) and the Vite dev server with hot-reload on [http://localhost:5173](http://localhost:5173). Press Ctrl+C to stop both.

**Production mode** (builds the frontend, then serves everything from FastAPI on :8000):

```bash
python start.py --prod
```

To regenerate TypeScript API types after changing the backend API:

```bash
python -c "import json, main; open('frontend/openapi.json','w').write(json.dumps(main.app.openapi()))"
cd frontend && npm run gen:api
```

## Usage Examples

| What you want | What to say |
|---|---|
| Add a media type | "Add Movies and Games as media types" |
| Track something you watched | "I watched Inception, 5 out of 5, it's a thriller" |
| Add something to watch later | "Add Dune Part Two to Movies, haven't seen it yet" |
| Rate something | "Update my Elden Ring rating to 4.5" |
| Get recommendations | "Recommend me some horror movies" |
| Browse your library | "Show me everything in my Games list" |
| Remove an item | "Remove Inception from Movies" |

## Project Structure

```
media_recommendations/
├── main.py            # FastAPI app: JSON API + serves the built SPA
├── schemas.py         # Pydantic request/response models
├── agent/
│   ├── loop.py        # Provider selector (reads LLM_PROVIDER from env)
│   ├── providers/     # gemini.py, groq.py — one file per LLM provider
│   ├── tools.py       # Tool registry (schema + handler, derived for each provider format)
│   ├── prompts.py     # System prompt
│   └── streaming.py   # SSE helper
├── database/          # SQLite: schema init + per-entity query functions
├── tmdb.py            # TMDB metadata lookup and caching
├── frontend/          # React + TypeScript + Vite
│   ├── src/
│   │   ├── api/       # Generated types + typed client + React Query hooks
│   │   ├── components/# Chat, sidebar, item modal, star rating, nav
│   │   ├── pages/     # ChatPage, BrowsePage
│   │   └── locales/   # UI strings (en, es)
│   └── dist/          # Production build (generated; served by FastAPI)
├── tests/             # Backend unit tests (pytest)
└── requirements.txt
```

## Notes

- Your media library is stored locally in `media.db`.
- Chat messages are sent to whichever LLM provider you configure. No other data leaves your machine.
- The assistant is scoped to media tracking and recommendations. It will decline off-topic requests.
