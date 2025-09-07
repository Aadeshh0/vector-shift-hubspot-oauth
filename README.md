# VectorShift Hubspot OAuth Integration Assignment

This project is an assignment provided by VectorShift, in which the task was to complete an OAuth integration with HubSpot. The integration was completed by implementing the following key functions in `hubspot.py`:
- authorize_hubspot
- oauth2callback_hubspot
- get_hubspot_credentials

The backend is built using a FastAPI backend and a React frontend. OAuth states and credentials were securely persisted in Redis to support the authentication flow during local development. The final implementation includes a fully functional HubSpot OAuth flow and data loading capability.

------------

### `Tech Stack`

- Backend : FastAPI (OAuth endpoints, data loading, token exchange), Uvicorn, Redis, httpx / requests
- Frontend : React with material UI and axios, 

## Prerequisites

- Python 3.10+ and pip  
- Node.js 18+ and npm  
- Redis (local or reachable via REDIS_HOST)

------------

## Setup Instructions

1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # on macOS
# .venv\Scripts\activate           # on windows
pip install -r requirements.txt
uvicorn main:app --reload
```

- Swagger UI: http://localhost:8000/docs  
- CORS allows http://localhost:3000 by default.

2. Frontend (React)

```bash
cd frontend
npm install
npm run start
```

- Development server: http://localhost:3000

3. Redis 

```bash
redis-server
```

----------

## HubSpot Configuration

- Set your HubSpot app’s Redirect URI to : http://localhost:8000/integrations/hubspot/oauth2callback
- Supply your HubSpot Client ID/Secret in backend/integrations/hubspot.py (or load from environment variables you introduce).
- Scopes used (typical): oauth, CRM objects read/write for contacts, companies, deals, and (optionally) custom objects.

------------

## Usage Instructions

1. Authorize with HubSpot
- In the frontend, select “Hubspot” and click “Connect to Hubspot”.
- Complete the OAuth flow in the popup with your HubSpot test app credentials.
- The backend stores state in Redis, exchanges the code for tokens, and saves credentials for the current user/org.

2. Load HubSpot Items
- Click “Load Data” in the UI to fetch items using the stored credentials.
- The frontend posts credentials to the HubSpot load route (see API Endpoints below).

3. View Results
- The UI renders a list of normalized IntegrationItems (name, id, type, created/modified dates).
- The full response is logged to the browser console for debugging.

------------

## API Endpoints (Backend)

HubSpot
- POST /integrations/hubspot/authorize : Begins the HubSpot OAuth flow: generates and stores a state token in Redis, then returns the provider authorization URL used by the frontend popup to request user consent.
- GET  /integrations/hubspot/oauth2callback : Handles the redirect after consent: validates state from Redis, exchanges the authorization code for tokens, stores credentials in Redis, and returns a small HTML page that closes the popup.
- POST /integrations/hubspot/credentials : Retrieves the saved HubSpot credentials for the given user_id and org_id from Redis so the client can use them to load data.
- POST /integrations/hubspot/get_hubspot_items : Loads HubSpot CRM objects (contacts, companies, deals, tickets) using the provided credentials JSON; normalizes results into IntegrationItems for display in the UI.

Use http://localhost:8000/docs (Swagger UI) to verify the endpoints are registered and test them directly.

