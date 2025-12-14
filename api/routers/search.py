"""
Search Router

Handles semantic search across different data sources (Jira, commits, code files, documents).
"""

import time
import json
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from fastapi.responses import StreamingResponse
from models import Query, User
from services.shared.auth import get_current_user
from services.infrastructure.database import db_service
from services.infrastructure.cache import SimpleCache
from services.domain.ai.conversation import SimpleConversation
from services.shared.streaming_utils import (
    StreamingEventFormatter, StreamingResponseBuilder, 
    create_streaming_headers, validate_streaming_request
)
from services.domain.search.streaming_search_service import StreamingSearchService
from dependencies.container import get_search_service, get_ai_service, get_qdrant_indexer

router = APIRouter(prefix="/search", tags=["search"])

# Initialize services
cache_service = SimpleCache()
conversation_service = SimpleConversation()

# Get qdrant indexer (may be None if not available)
try:
    qdrant_indexer = None  # Will be initialized in endpoints
except Exception:
    qdrant_indexer = None


async def perform_search(query: Query, current_user: User):
    """
    Perform comprehensive search across all data sources.
    
    Returns search results and metadata for both streaming and non-streaming responses.
    """
    # Get conversation context
    context_history = conversation_service.get_context(query.session_id) if query.session_id else ""
    
    # Search documentation
    try:
        search_service = await get_search_service()
        doc_results = await search_service.enhanced_search(
            query.question, 
            query.search_type, 
            query.max_results, 
            current_user.organization_id
        )
    except Exception as e:
        print(f"Error searching docs: {e}")
        doc_results = []
    
    # Search Jira tickets semantically
    try:
        try:
            qdrant_indexer = await get_qdrant_indexer()
            if qdrant_indexer:
                jira_tickets = await qdrant_indexer.search_jira_tickets(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
                print(f"🔍 Found {len(jira_tickets)} Jira tickets (semantic) for: {query.question}")
            else:
                raise Exception("Qdrant indexer not available")
        except Exception:
            # Fallback to PostgreSQL exact search
            jira_tickets = await db_service.search_jira_tickets(
                query.question,
                current_user.organization_id,
                limit=3
            )
            print(f"Found {len(jira_tickets)} Jira tickets (exact) for: {query.question}")
    except Exception as e:
        print(f"Error searching Jira tickets: {e}")
        jira_tickets = []

    # Search commits semantically
    try:
        try:
            qdrant_indexer = await get_qdrant_indexer()
            if qdrant_indexer:
                commit_results = await qdrant_indexer.search_commits(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
                print(f"🔍 Found {len(commit_results)} commits (semantic) for: {query.question}")
            else:
                commit_results = []
        except Exception:
            commit_results = []
    except Exception as e:
        print(f"Error searching commits: {e}")
        commit_results = []

    # Search code files semantically
    try:
        try:
            qdrant_indexer = await get_qdrant_indexer()
            if qdrant_indexer:
                code_files = await qdrant_indexer.search_code_files(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
                print(f"🔍 Found {len(code_files)} code files (semantic) for: {query.question}")
            else:
                raise Exception("Qdrant indexer not available")
        except Exception:
            # Fallback to PostgreSQL exact search
            code_files = await db_service.search_code_files(
                query.question,
                current_user.organization_id,
                limit=3
            )
    except Exception as e:
        print(f"Error searching code files: {e}")
        code_files = []

    # Combine all sources for context
    all_sources = []
    
    # Add documentation results
    for doc in doc_results:
        # Handle both dict and ScoredPoint objects
        if hasattr(doc, 'payload'):
            # Qdrant ScoredPoint object
            all_sources.append({
                "type": "documentation",
                "title": doc.payload.get("title", "Unknown Document"),
                "content": doc.payload.get("content", "")[:500],
                "score": doc.score if hasattr(doc, 'score') else 0.0
            })
        else:
            # Dict object
            all_sources.append({
                "type": "documentation",
                "title": doc.get("title", "Unknown Document"),
                "content": doc.get("content", "")[:500],
                "score": doc.get("score", 0.0)
            })
    
    # Add Jira ticket results
    for ticket in jira_tickets:
        all_sources.append({
            "type": "jira_ticket",
            "title": f"{ticket.get('ticket_key', 'Unknown')}: {ticket.get('summary', 'No summary')}",
            "content": ticket.get('description', '')[:500],
            "score": ticket.get('score', 0.0),
            "metadata": {
                "ticket_key": ticket.get('ticket_key'),
                "status": ticket.get('status'),
                "priority": ticket.get('priority')
            }
        })
    
    # Add commit results
    for commit in commit_results:
        all_sources.append({
            "type": "commit",
            "title": f"Commit: {commit.get('message', 'No message')[:50]}",
            "content": f"SHA: {commit.get('sha', 'unknown')[:7]}\nMessage: {commit.get('message', '')}",
            "score": commit.get('score', 0.0),
            "metadata": {
                "sha": commit.get('sha'),
                "author": commit.get('author_name')
            }
        })
    
    # Add code file results
    for file in code_files:
        all_sources.append({
            "type": "code_file",
            "title": f"File: {file.get('file_path', 'Unknown file')}",
            "content": file.get('content', '')[:500],
            "score": file.get('score', 0.0),
            "metadata": {
                "file_path": file.get('file_path'),
                "language": file.get('language')
            }
        })
    
    # Sort by relevance score
    all_sources.sort(key=lambda x: x.get('score', 0.0), reverse=True)
    
    # Limit to top results
    top_sources = all_sources[:query.max_results]
    
    return top_sources, context_history


# Removed - now using StreamingEventFormatter from streaming_utils


async def generate_streaming_search_response(
    query: Query, 
    current_user: User, 
    top_sources: list, 
    context_history: str,
    start_time: float
) -> AsyncGenerator[str, None]:
    """Generate streaming response with search context using proper event models."""
    builder = StreamingResponseBuilder()
    
    try:
        # Validate streaming request
        validation = validate_streaming_request(query.dict())
        if not validation["valid"]:
            yield await builder.send_error(
                error_type="validation_error",
                message=validation["error"],
                recoverable=False,
                error_code="INVALID_STREAMING_REQUEST"
            )
            return
        
        # Send initial metadata
        sources_searched = {
            "documentation": len([s for s in top_sources if s['type'] == 'documentation']),
            "jira_tickets": len([s for s in top_sources if s['type'] == 'jira_ticket']),
            "commits": len([s for s in top_sources if s['type'] == 'commit']),
            "code_files": len([s for s in top_sources if s['type'] == 'code_file'])
        }
        
        yield await builder.send_metadata(
            sources_searched=sources_searched,
            total_results=len(top_sources)
        )
        
        # Send search sources
        yield await builder.send_sources(top_sources)
        
        # Generate AI response with context
        ai_service = await get_ai_service()
        
        # Build context from search results
        context_parts = []
        if context_history:
            context_parts.append(f"Previous conversation:\n{context_history}")
        
        if top_sources:
            context_parts.append("Relevant information found:")
            for i, source in enumerate(top_sources[:5], 1):
                context_parts.append(f"{i}. [{source['type']}] {source['title']}")
                context_parts.append(f"   {source['content']}")
        
        context = "\n\n".join(context_parts)
        
        # Create prompt
        prompt = f"""Based on the following context, please answer the user's question comprehensively and accurately.

Context:
{context}

Question: {query.question}

Please provide a helpful and detailed answer based on the available information. If the context doesn't contain enough information to fully answer the question, please say so and suggest what additional information might be needed."""

        # Stream AI response with chunk tracking
        full_response = ""
        chunk_count = 0
        
        async for chunk in ai_service.generate_streaming_response(
            prompt=prompt,
            model=query.model or "mistral",
            temperature=0.7
        ):
            full_response += chunk
            chunk_count += 1
            
            yield await builder.send_content_chunk(
                chunk=chunk,
                chunk_id=chunk_count
            )
        
        # Send completion event
        query_metadata = {
            "question": query.question,
            "search_type": query.search_type,
            "sources_found": sources_searched,
            "chunks_sent": chunk_count
        }
        
        yield await builder.send_completion(
            total_tokens=len(full_response.split()),
            model_used=query.model,
            query_metadata=query_metadata
        )
        
        # Update conversation history
        if query.session_id:
            conversation_service.add_message(query.session_id, query.question, full_response, top_sources)
            
    except Exception as e:
        yield await builder.send_error(
            error_type="streaming_error",
            message=str(e),
            recoverable=True,
            error_code="STREAMING_GENERATION_ERROR"
        )


@router.post("/ask")
async def ask(query: Query, current_user: User = Depends(get_current_user)):
    """
    Main search and AI query endpoint.
    
    Performs semantic search across all data sources and generates AI responses.
    Supports both streaming and non-streaming responses based on the 'stream' parameter.
    """
    start_time = time.time()
    
    # Check quota
    if not await db_service.check_and_increment_quota(current_user.organization_id):
        raise HTTPException(status_code=429, detail="Monthly quota exceeded")
    
    # Log API request for tracking
    await db_service.log_audit(current_user.id, current_user.organization_id, "api_request", "ask", {"question": query.question[:100]})
    
    try:
        # Check cache for non-streaming requests
        if not query.stream:
            cached_result = cache_service.get(query.question)
            if cached_result:
                return cached_result
        
        # Perform search across all data sources
        top_sources, context_history = await perform_search(query, current_user)
        
        # Handle streaming response
        if query.stream:
            streaming_service = StreamingSearchService()
            return StreamingResponse(
                streaming_service.generate_streaming_response(query, current_user),
                media_type="text/event-stream",
                headers=create_streaming_headers()
            )
        
        # Handle non-streaming response
        # Generate AI response for non-streaming
        try:
            ai_service = await get_ai_service()
            
            # Build context from search results
            context_parts = []
            if context_history:
                context_parts.append(f"Previous conversation:\n{context_history}")
            
            if top_sources:
                context_parts.append("Relevant information found:")
                for i, source in enumerate(top_sources[:5], 1):
                    context_parts.append(f"{i}. [{source['type']}] {source['title']}")
                    context_parts.append(f"   {source['content']}")
            
            context = "\n\n".join(context_parts)
            
            # Create prompt
            prompt = f"""Based on the following context, please answer the user's question comprehensively and accurately.

Context:
{context}

Question: {query.question}

Please provide a helpful and detailed answer based on the available information. If the context doesn't contain enough information to fully answer the question, please say so and suggest what additional information might be needed."""

            ai_response = await ai_service.generate_response(prompt, query.model)
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            ai_response = "I apologize, but I encountered an error while generating a response. Please try again."
        
        # Build final response
        response = {
            "answer": ai_response,
            "sources": top_sources,
            "query_metadata": {
                "question": query.question,
                "search_type": query.search_type,
                "model_used": query.model,
                "processing_time": time.time() - start_time,
                "sources_found": {
                    "documentation": len([s for s in top_sources if s['type'] == 'documentation']),
                    "jira_tickets": len([s for s in top_sources if s['type'] == 'jira_ticket']),
                    "commits": len([s for s in top_sources if s['type'] == 'commit']),
                    "code_files": len([s for s in top_sources if s['type'] == 'code_file'])
                }
            }
        }
        
        # Cache the result
        cache_service.set(query.question, response)
        
        # Update conversation history
        if query.session_id:
            conversation_service.add_message(query.session_id, query.question, ai_response, top_sources)
        
        return response
        
    except Exception as e:
        print(f"Error in ask endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/jira")
async def search_jira_tickets_semantic(
    query: str,
    limit: int = QueryParam(default=10, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Search Jira tickets using semantic similarity.
    
    Uses vector embeddings to find tickets similar to the query.
    """
    try:
        qdrant_indexer = await get_qdrant_indexer()
        if not qdrant_indexer:
            raise HTTPException(status_code=503, detail="Semantic search not available")
        
        results = await qdrant_indexer.search_jira_tickets(
            query,
            current_user.organization_id,
            limit=limit
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commits")
async def search_commits_semantic(
    query: str,
    limit: int = QueryParam(default=10, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Search commits using semantic similarity.
    
    Uses vector embeddings to find commits similar to the query.
    """
    try:
        qdrant_indexer = await get_qdrant_indexer()
        if not qdrant_indexer:
            raise HTTPException(status_code=503, detail="Semantic search not available")
        
        results = await qdrant_indexer.search_commits(
            query,
            current_user.organization_id,
            limit=limit
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/code")
async def search_code_files_semantic(
    query: str,
    limit: int = QueryParam(default=10, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Search code files using semantic similarity.
    
    Uses vector embeddings to find code files similar to the query.
    """
    try:
        try:
            qdrant_indexer = await get_qdrant_indexer()
            if qdrant_indexer:
                results = await qdrant_indexer.search_code_files(
                    query,
                    current_user.organization_id,
                    limit=limit
                )
            else:
                raise Exception("Qdrant indexer not available")
        except Exception:
            # Fallback to PostgreSQL search
            results = await db_service.search_code_files(
                query,
                current_user.organization_id,
                limit=limit
            )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))