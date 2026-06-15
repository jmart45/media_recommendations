# Media Recommendations

A personal media tracking and recommendation app powered by Claude. Chat naturally to track movies, games, music, books, or any other media — along with your ratings — and get personalized recommendations based on what you've enjoyed.

## Features

- **Chat interface** — add and manage media through natural conversation
- **Media types** — create custom categories (Movies, Games, Music, Books, etc.)
- **Ratings** — rate media 0–5, or mark items as not yet seen/played
- **Genres** — tag items by genre and filter recommendations (e.g. "recommend me a horror movie")
- **Recommendations** — Claude references your rated media to suggest what to watch or play next
- **Media sidebar** — browse your full library at a glance, organized by type
- **Browse page** — open a sortable, filterable table of any media type via the arrow link in the sidebar, with posters, descriptions, and ratings from [TMDB](https://www.themoviedb.org/) (optional)

## Prerequisites

- Python 3.12 or newer
- Node.js 20 or newer (for the React frontend)
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

Optionally, add a [TMDB API key](https://www.themoviedb.org/settings/api) (free) to show posters, descriptions, and TMDB ratings on the Browse page. Either the v3 "API Key" or the v4 "API Read Access Token" works:

```
TMDB_API_KEY=...
```

**4. Build the frontend**

```bash
cd frontend
npm install
npm run build
cd ..
```

**5. Start the server**

```bash
python -m uvicorn main:app --reload
```

**6. Open the app**

Navigate to [http://localhost:8000](http://localhost:8000) in your browser. FastAPI
serves the built React app from `frontend/dist`.

### Development

For frontend work with hot-reload, run two processes: the API and the Vite dev server.

```bash
# terminal 1 — API
python -m uvicorn main:app --reload

# terminal 2 — frontend (proxies /api to :8000)
cd frontend && npm run dev
```

Then open the Vite URL (default [http://localhost:5173](http://localhost:5173)).

The frontend's TypeScript API types are generated from the backend's OpenAPI
schema. To refresh them after changing the API, dump the schema and regenerate:

```bash
python -c "import json, main; open('frontend/openapi.json','w').write(json.dumps(main.app.openapi()))"
cd frontend && npm run gen:api
```

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
├── main.py            # FastAPI app: JSON API + serves the built SPA
├── schemas.py         # Pydantic request/response models (the API contract)
├── agent/             # Claude agent loop, tool registry, prompts
├── database/          # SQLite: connection/schema + per-entity queries
├── tmdb.py            # TMDB metadata lookup and caching
├── frontend/          # React + TypeScript + Vite app
│   ├── src/
│   │   ├── api/       # generated types + typed client + React Query hooks
│   │   ├── components/# nav, sidebar, chat, item modal, star rating
│   │   ├── pages/     # ChatPage, BrowsePage
│   │   └── locales/   # UI translations (en, es)
│   └── dist/          # production build (generated; served by FastAPI)
├── tests/             # Backend unit + API tests
├── requirements.txt
├── .env               # Your API keys (not committed)
└── .env.example       # Template for API key setup
```

## Notes

- Your media library is stored locally in `media.db` — no data is sent anywhere except your chat messages to the Anthropic API.
- The assistant is restricted to media tracking and recommendations. It will decline off-topic requests.
- Each person running the app uses their own API key and gets their own local database.
