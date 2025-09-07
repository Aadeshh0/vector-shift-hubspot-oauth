# VectorShift Hubspot OAuth Integrations Assignment

This project is an assignment provided by Vector Shift, that asked us to complete OAuth integration with HubSpot,
completing the functions authorize_hubspot, oauth2callback_hubspot, and get_hubspot_credentials functions in 
hubspot.py using a FastAPI backend and a React frontend, persisting OAuth states and credentials in Redis for secure
flows during local development. It includes a working HubSpot OAuth flow and data loading.

------------

### `Tech Stack`

#### - Backend : FastAPI (OAuth endpoints, data loading, token exchange), Uvicorn, Redis, httpx / requests
#### - Frontend : React with material UI and axios, 

## Prerequisites

- Python 3.10+ and pip  
- Node.js 18+ and npm  
- Redis (local or reachable via REDIS_HOST)

------------

## Setup Instructions

1. Backend (FastAPI)

```bash
cd backend
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
- POST /integrations/hubspot/authorize
- GET  /integrations/hubspot/oauth2callback
- POST /integrations/hubspot/credentials
- POST /integrations/hubspot/get_hubspot_items   ← used by the current frontend build

Use http://localhost:8000/docs (Swagger UI) to verify the endpoints are registered and test them directly.

