import os
import httpx
from typing import Optional, Dict
from fastapi import HTTPException
import jwt
from datetime import datetime

class OAuthService:
    def __init__(self):
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.microsoft_client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.microsoft_client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8501/auth/callback")
    
    def get_google_auth_url(self) -> str:
        """Get Google OAuth authorization URL"""
        if not self.google_client_id:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        
        params = {
            "client_id": self.google_client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/auth?{query_string}"
    
    def get_microsoft_auth_url(self) -> str:
        """Get Microsoft OAuth authorization URL"""
        if not self.microsoft_client_id:
            raise HTTPException(status_code=500, detail="Microsoft OAuth not configured")
        
        params = {
            "client_id": self.microsoft_client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "response_mode": "query"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{query_string}"
    
    async def exchange_google_code(self, code: str) -> Optional[Dict]:
        """Exchange Google authorization code for user info"""
        if not all([self.google_client_id, self.google_client_secret]):
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri
                }
            )
            
            if token_response.status_code != 200:
                return None
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                return None
            
            # Get user info
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                return None
            
            user_data = user_response.json()
            return {
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "provider": "google",
                "provider_id": user_data.get("id")
            }
    
    async def exchange_microsoft_code(self, code: str) -> Optional[Dict]:
        """Exchange Microsoft authorization code for user info"""
        if not all([self.microsoft_client_id, self.microsoft_client_secret]):
            raise HTTPException(status_code=500, detail="Microsoft OAuth not configured")
        
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "client_id": self.microsoft_client_id,
                    "client_secret": self.microsoft_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri
                }
            )
            
            if token_response.status_code != 200:
                return None
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                return None
            
            # Get user info
            user_response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                return None
            
            user_data = user_response.json()
            return {
                "email": user_data.get("mail") or user_data.get("userPrincipalName"),
                "name": user_data.get("displayName"),
                "provider": "microsoft",
                "provider_id": user_data.get("id")
            }

# Global OAuth service
oauth_service = OAuthService()