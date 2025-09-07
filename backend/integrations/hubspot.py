import httpx
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import asyncio
import base64
import requests
from .integration_item import IntegrationItem
from urllib.parse import urlencode, unquote_plus
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

CLIENT_ID = 'fbcbe6f5-9630-4d89-be5e-a77ff320218a'
CLIENT_SECRET = '905bf1b9-5b60-40a5-9fe3-0c922baec70f'
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
authorization_url = 'https://app.hubspot.com/oauth/authorize'
token_url = 'https://api.hubapi.com/oauth/v1/token'

HUBSPOT_SCOPES = [
    "oauth",
    "crm.objects.companies.read",
    "crm.objects.companies.write",
    "crm.objects.contacts.read",
    "crm.objects.contacts.write",
    "crm.objects.custom.read",
    "crm.objects.custom.write",
    "crm.objects.deals.read",
    "crm.objects.deals.write"
]

async def authorize_hubspot(user_id, org_id):
    state_token = secrets.token_urlsafe(32)
    state_data = {
        'state': state_token,
        'user_id': user_id,
        'org_id': org_id,
    }
    
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600)

    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(HUBSPOT_SCOPES),  
        'state': encoded_state,
        'response_type': 'code'
    }

    auth_url = f"{authorization_url}?{urlencode(params)}"

    print(f"Generated OAuth URL: {auth_url}")
    print(f"State token: {state_token}")
    print(f"Encoded state: {encoded_state}")
    return auth_url

async def oauth2callback_hubspot(request: Request):
    try:
        #check for any ouath error
        if request.query_params.get('error'):  
            print(f"OAuth error: {request.query_params.get('error')}")
            raise HTTPException(status_code=400, detail=request.query_params.get('error'))
        
        code = request.query_params.get('code')
        encoded_state = request.query_params.get('state')
        
        print(f"Received code: {code}")
        print(f"Received encoded state: {encoded_state}")
        
        if not code:
            raise HTTPException(status_code=400, detail='No authorization code received')
        
        if not encoded_state:
            raise HTTPException(status_code=400, detail='No state parameter found')
        
        try:
            decoded_state = base64.urlsafe_b64decode(encoded_state.encode()).decode()
            print(f"Decoded state: {decoded_state}")
            state_data = json.loads(decoded_state)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error decoding state: {e}")
            raise HTTPException(status_code=400, detail=f'Invalid state parameter: {str(e)}')

        original_state = state_data.get('state')
        user_id = state_data.get('user_id')
        org_id = state_data.get('org_id')

        print(f"Extracted user_id: {user_id}, org_id: {org_id}, state: {original_state}")

        saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
        
        if not saved_state:
            print("No saved state found in Redis")
            raise HTTPException(status_code=400, detail='State not found or expired')
        
        try:
            saved_state_data = json.loads(saved_state)
        except json.JSONDecodeError:
            print("Error decoding saved state")
            raise HTTPException(status_code=400, detail='Invalid saved state')

        if original_state != saved_state_data.get('state'):
            print(f"State mismatch: {original_state} != {saved_state_data.get('state')}")
            raise HTTPException(status_code=400, detail='State does not match')
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
        
        print(f"Token exchange data: {token_data}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=token_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',  
                }
            )
            
            print(f"Token response status: {response.status_code}")
            print(f"Token response text: {response.text}")

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f'Token exchange failed: {response.text}')

        token_response = response.json()
        print(f"Token response: {token_response}")

        await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(token_response), expire=3600)
        
        await delete_key_redis(f'hubspot_state:{org_id}:{user_id}')

        close_window_script = """
        <html>
            <head><title>Authorization Complete</title></head>
            <body>
                <h2>Hubspot Authorization successful!</h2>
                <p>You can close this window and return to the application now.</p>
                <script>
                    setTimeout(() => {
                        window.close();
                    }, 2000);
                </script>
            </body>
        </html>
        """

        return HTMLResponse(content=close_window_script)
        
    except Exception as e:
        print(f"Error in oauth2callback_hubspot: {str(e)}")
        error_html = f"""
        <html>
            <head><title>Authorization Error</title></head>
            <body>
                <h2>Authorization failed</h2>
                <p>Error: {str(e)}</p>
                <p>You can close this window and try again.</p>
            </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=400)

async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    return credentials

async def create_integration_item_metadata_object(response_json, schema):
    properties = response_json.get('properties', {})
    item_id = response_json.get('id')
    created_time = response_json.get('createdAt') 
    updated_time = response_json.get('updatedAt')

    if schema == 'companies':
        name = properties.get('name', 'Unnamed Company')
        return IntegrationItem(
            id=f"{item_id}_{schema}",
            type=schema,
            name=name,
            creation_time=created_time,
            last_modified_time=updated_time,
        )
    
    elif schema == 'contacts':
        firstname = properties.get('firstname', '')
        lastname = properties.get('lastname', '')
        name = f'{firstname} {lastname}'.strip()
        if not name:
            name = properties.get('email', 'Unnamed Contact')
        return IntegrationItem(
            id=f"{item_id}_{schema}",
            type=schema,
            name=name,
            creation_time=created_time,
            last_modified_time=updated_time,
        )
    
    elif schema == 'deals':
        name = properties.get("dealname", 'Unnamed Deal')
        return IntegrationItem(
            id=f"{item_id}_{schema}",
            type=schema,
            name=name,
            creation_time=created_time,
            last_modified_time=updated_time,
        )
    
    elif schema == 'tickets':
        name = properties.get("dealname", "Unnamed Deal")
        return IntegrationItem(
            id=f"{item_id}_{schema}",
            type=schema,
            name=name,
            creation_time=created_time,
            last_modified_time=updated_time,
        )
    
    else:  # tickets
        name = f'Unknown {schema}'
        return IntegrationItem(
            id=f"{item_id}_{schema}",
            type=schema,
            name=name,
            creation_time=created_time,
            last_modified_time=updated_time,
        )

def fetch_hubspot_data(access_token, object_type):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    endpoint = f'https://api.hubapi.com/crm/v3/objects/{object_type}'
    
    try:
        response = requests.get(endpoint, headers=headers)
        
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error fetching {object_type}: Status {response.status_code}, Message: {response.text}')
            return None
            
    except Exception as e:
        print(f'Exception while fetching {object_type}: {str(e)}')
        return None

async def get_items_hubspot(credentials):    
    try:
        print(f"get_items_hubspot called with credentials: {credentials}")
        print(f"get_items_hubspot called with credentials type: {type(credentials)}")
        
        if isinstance(credentials, str):
            credentials = json.loads(credentials)
        
        access_token = credentials.get('access_token')

        if not access_token:
            print("No access token found in credentials")
            raise HTTPException(status_code=400, detail='No access token found in credentials')

        print(f"Using access token: {access_token[:20]}...")

        default_objects = ['contacts', 'companies', 'deals', 'tickets']
        list_of_integration_item_metadata = []

        for object_type in default_objects:
            print(f'Fetching {object_type}...')
            api_response = fetch_hubspot_data(access_token, object_type)
            
            if api_response and 'results' in api_response:
                results = api_response['results']
                print(f'Found {len(results)} {object_type}')
                
                for item in results:
                    try:
                        integration_item = await create_integration_item_metadata_object(item, object_type)
                        item_dict = {
                            'id': integration_item.id,
                            'type': integration_item.type,
                            'name': integration_item.name,
                            'creation_time': integration_item.creation_time,
                            'last_modified_time': integration_item.last_modified_time,
                        }
                        list_of_integration_item_metadata.append(item_dict)
                    except Exception as item_error:
                        print(f"Error processing item {item.get('id', 'unknown')}: {item_error}")
                        continue
            else:
                print(f'No results found for {object_type}')

        print(f'Total integration items: {len(list_of_integration_item_metadata)}')
        
        if list_of_integration_item_metadata:
            print(f'Sample items: {list_of_integration_item_metadata[:2]}')
        
        return {
            'total_items': len(list_of_integration_item_metadata),
            'items': list_of_integration_item_metadata,
            'message': f'Successfully retrieved {len(list_of_integration_item_metadata)} items from HubSpot'
        }
        
    except Exception as e:
        print(f"Error in get_items_hubspot: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f'Error fetching HubSpot items: {str(e)}')