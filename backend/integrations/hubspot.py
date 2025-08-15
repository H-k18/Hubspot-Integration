import os
import json
import secrets
import httpx
import asyncio
import base64
from typing import List
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse

# CORRECTED IMPORTS to match your project structure
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# --- Configuration ---
# IMPORTANT: Use environment variables for your Client ID and Secret.
HUBSPOT_CLIENT_ID = os.environ.get("HUBSPOT_CLIENT_ID", "YOUR_HUBSPOT_CLIENT_ID")
HUBSPOT_CLIENT_SECRET = os.environ.get("HUBSPOT_CLIENT_SECRET", "YOUR_HUBSPOT_CLIENT_SECRET")

# This must match the Redirect URI in your HubSpot App settings
REDIRECT_URI = "http://localhost:8000/integrations/hubspot/oauth2callback"

# Scopes determine the permissions your app is requesting.
SCOPES = "crm.objects.contacts.read"


async def authorize_hubspot(user_id: str, org_id: str):
    """
    Part 1: Creates a secure authorization URL for HubSpot.
    This follows the same state management pattern as airtable.py.
    """
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    # Encode the state data to be safely passed in a URL
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')
    
    # Store the state in Redis to verify it in the callback
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600)

    auth_url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&state={encoded_state}"
    )
    return auth_url


async def oauth2callback_hubspot(request: Request):
    """
    Part 1: Handles the callback from HubSpot after user authorization.
    Exchanges the authorization code for an access token.
    """
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error_description'))

    code = request.query_params.get("code")
    encoded_state = request.query_params.get('state')
    
    # Decode state and retrieve user/org info
    state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode('utf-8'))
    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    # Verify state from Redis to prevent CSRF attacks
    saved_state_str = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    if not saved_state_str or original_state != json.loads(saved_state_str).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    # Exchange authorization code for an access token using httpx for async request
    token_url = "https://api.hubapi.com/oauth/v1/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": HUBSPOT_CLIENT_ID,
        "client_secret": HUBSPOT_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    
    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(token_url, data=payload),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}') # Clean up the state from Redis
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Error retrieving access token: {response.text}")

    # Store the new credentials in Redis with user and org IDs
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=3600)
    
    # Return a script to close the OAuth popup window, matching the existing pattern
    return HTMLResponse(content="<html><script>window.close();</script></html>")


async def get_hubspot_credentials(user_id: str, org_id: str):
    """
    Part 1: Retrieves credentials from Redis for the frontend.
    This follows the "get and delete" pattern from airtable.py.
    """
    credentials_key = f'hubspot_credentials:{org_id}:{user_id}'
    credentials = await get_value_redis(credentials_key)
    if not credentials:
        raise HTTPException(status_code=400, detail='No HubSpot credentials found.')
    
    await delete_key_redis(credentials_key)
    return json.loads(credentials)


async def get_items_hubspot(credentials: str) -> List[IntegrationItem]:
    """
    Part 2: Fetches contacts from HubSpot and maps them to IntegrationItem objects.
    """
    credentials_json = json.loads(credentials)
    access_token = credentials_json.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Access token not found in credentials.")

    api_url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"properties": "firstname,lastname,email"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers, params=params)

    if response.status_code != 200:
        # As per instructions, print errors to the console
        print(f"Error fetching HubSpot contacts: {response.text}")
        return []

    data = response.json()
    items = []
    
    for contact in data.get("results", []):
        properties = contact.get("properties", {})
        first_name = properties.get("firstname", "")
        last_name = properties.get("lastname", "")
        
        # Map HubSpot contact data to your IntegrationItem model
        items.append(
            IntegrationItem(
                id=contact.get("id"),
                name=f"{first_name} {last_name}".strip(),
                type="HubSpot Contact" # Descriptive type
            )
        )
    
    # As suggested, printing the final list to the console
    print(f"--- Fetched {len(items)} HubSpot Items ---")
    print([item.__dict__ for item in items])
    print("---------------------------------------")
    
    return items