import requests
import streamlit as st
from typing import Optional, Dict
from config import API_URL

class AuthService:
    def __init__(self):
        self.api_url = API_URL
    
    def login(self, email: str, password: str) -> Optional[Dict]:
        """Login user"""
        try:
            print(f"UI: Attempting login for {email} to {self.api_url}/auth/login")
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"email": email, "password": password},
                timeout=30
            )
            print(f"UI: Response status: {response.status_code}")
            print(f"UI: Response text: {response.text[:500]}...")  # Truncate long responses
            
            if response.status_code == 200:
                json_response = response.json()
                print(f"UI: Parsed JSON keys: {list(json_response.keys())}")
                return json_response
            else:
                print(f"UI: Non-200 status code: {response.status_code}")
                return None
        except Exception as e:
            print(f"UI: Login exception: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def register(self, email: str, password: str, name: str, organization_name: str) -> Optional[Dict]:
        """Register new user"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "name": name,
                    "organization_name": organization_name
                }
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    def get_google_auth_url(self) -> Optional[str]:
        """Get Google OAuth URL"""
        try:
            response = requests.get(f"{self.api_url}/auth/google")
            if response.status_code == 200:
                return response.json().get("auth_url")
            return None
        except Exception:
            return None
    
    def get_microsoft_auth_url(self) -> Optional[str]:
        """Get Microsoft OAuth URL"""
        try:
            response = requests.get(f"{self.api_url}/auth/microsoft")
            if response.status_code == 200:
                return response.json().get("auth_url")
            return None
        except Exception:
            return None
    
    def get_current_user(self, token: str) -> Optional[Dict]:
        """Get current user info"""
        try:
            response = requests.get(
                f"{self.api_url}/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    def logout(self):
        """Logout user"""
        if "auth_token" in st.session_state:
            del st.session_state.auth_token
        if "user_info" in st.session_state:
            del st.session_state.user_info
        st.rerun()

# Global auth service
auth_service = AuthService()