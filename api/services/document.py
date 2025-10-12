import requests
import socket
import ipaddress
from typing import List, Tuple
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from fastapi import HTTPException
from qdrant_client.models import PointStruct
from uuid import uuid4
from datetime import datetime
from config import COLLECTION_NAME
from .encryption import encryption_service
from .search import extract_keywords

def clean_html(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(separator="\n")

def chunk_text(text: str, max_chunk_size: int = 1000) -> List[str]:
    return [text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]

def validate_url(url: str) -> bool:
    """Validate URL to prevent SSRF attacks"""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
            
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved:
                return False
        except ValueError:
            if hostname.lower() in ['localhost', 'localhost.localdomain']:
                return False
                
        return True
    except (ValueError, AttributeError):
        return False

class DocumentService:
    def __init__(self, qdrant_client, embedder):
        self.qdrant = qdrant_client
        self.embedder = embedder
    
    def get_collection_name(self, organization_id: str) -> str:
        """Get organization-specific collection name"""
        return f"{COLLECTION_NAME}_{organization_id}"
    
    def ensure_collection_exists(self, organization_id: str):
        """Create organization-specific collection if it doesn't exist"""
        collection_name = self.get_collection_name(organization_id)
        if collection_name not in [col.name for col in self.qdrant.get_collections().collections]:
            self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config={"size": self.embedder.get_sentence_embedding_dimension(), "distance": "Cosine"},
            )
            
            try:
                self.qdrant.create_payload_index(
                    collection_name=collection_name,
                    field_name="keywords",
                    field_schema="keyword"
                )
                self.qdrant.create_payload_index(
                    collection_name=collection_name,
                    field_name="text",
                    field_schema="text"
                )
            except Exception:
                pass
    
    def store_chunks(self, title: str, chunks: List[str], source_type: str, organization_id: str) -> None:
        """Store encrypted text chunks in organization-specific collection"""
        collection_name = self.get_collection_name(organization_id)
        
        for i, chunk in enumerate(chunks):
            embedding = self.embedder.encode(chunk).tolist()
            keywords = extract_keywords(chunk)
            
            # Encrypt sensitive data
            encrypted_text = encryption_service.encrypt_data(chunk, organization_id)
            encrypted_title = encryption_service.encrypt_data(title, organization_id)
            
            self.qdrant.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=str(uuid4()),
                        vector=embedding,
                        payload={
                            "title": encrypted_title, 
                            "text": encrypted_text,
                            "keywords": keywords,  # Keep unencrypted for search
                            "chunk_index": i,
                            "created_at": datetime.now().isoformat(),
                            "source_type": source_type,
                            "organization_id": organization_id
                        },
                    )
                ],
            )
    
    def fetch_confluence_pages(self, space_key: str, base_url: str, username: str, token: str) -> List[Tuple[str, str]]:
        """Fetch all pages from Confluence space"""
        # Normalize base URL - remove trailing slashes and ensure correct format
        base_url = base_url.rstrip('/')

        # For Atlassian Cloud, the API endpoint is under /wiki
        # Check if it's a cloud instance (*.atlassian.net)
        if 'atlassian.net' in base_url and '/wiki' not in base_url:
            base_url = f"{base_url}/wiki"

        url = f"{base_url}/rest/api/content"
        params = {"spaceKey": space_key, "expand": "body.storage", "limit": 100}
        auth = (username, token)
        
        pages = []
        while url:
            try:
                r = requests.get(url, params=params, auth=auth, timeout=30)
                r.raise_for_status()
                data = r.json()
                for page in data.get("results", []):
                    html = page["body"]["storage"]["value"]
                    text = clean_html(html)
                    pages.append((page["title"], text))
                next_link = data.get("_links", {}).get("next")
                if next_link:
                    url = base_url + next_link
                    params = None
                else:
                    url = None
            except requests.RequestException as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch Confluence data: {str(e)}")
        return pages
    
    def sync_public_url(self, url: str, organization_id: str) -> dict:
        """Sync content from public URL with organization isolation"""
        if not validate_url(url):
            raise HTTPException(status_code=400, detail="Invalid or unsafe URL provided")

        try:
            resolved_ip = socket.gethostbyname(urlparse(url).hostname)
            ip = ipaddress.ip_address(resolved_ip)
            if ip.is_private or ip.is_loopback or ip.is_reserved:
                raise HTTPException(status_code=400, detail="Access to private/internal resources not allowed")
        except (socket.gaierror, ValueError):
            raise HTTPException(status_code=400, detail="Invalid hostname")
            
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            texts = soup.find_all(["p", "h1", "h2", "h3", "li"])
            full_text = "\n".join(t.get_text() for t in texts)

            chunks = chunk_text(full_text)
            self.store_chunks(url, chunks, "public", organization_id)
            return {"status": "synced", "url": url, "chunks": len(chunks)}
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch URL: {str(e)}")