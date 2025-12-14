"""
Streaming Search Service

Provides comprehensive streaming search functionality with proper integration
of all data sources (Jira, commits, code, docs) and AI response generation.
"""

import time
import asyncio
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
from models import Query, User, SearchSource
from services.shared.streaming_utils import StreamingResponseBuilder, StreamingEventFormatter
from services.shared.streaming_error_handler import (
    streaming_fallback_manager, handle_streaming_error, create_error_response
)
from services.infrastructure.database import db_service
from services.domain.ai.conversation import SimpleConversation
from dependencies.container import get_search_service, get_ai_service, get_qdrant_indexer

logger = logging.getLogger(__name__)


class StreamingSearchService:
    """
    Service for handling streaming search responses with full context integration.
    
    Integrates existing search logic (Jira, commits, code, docs) with streaming
    and maintains search result processing and context building.
    """
    
    def __init__(self):
        self.conversation_service = SimpleConversation()
    
    async def perform_comprehensive_search(
        self, 
        query: Query, 
        current_user: User
    ) -> tuple[List[Dict[str, Any]], str]:
        """
        Perform comprehensive search across all data sources.
        
        Returns:
            Tuple of (search_results, conversation_context)
        """
        # Get conversation context
        context_history = ""
        if query.session_id:
            context_history = self.conversation_service.get_context(query.session_id)
        
        # Initialize results collection
        all_sources = []
        
        # Search documentation
        try:
            search_service = await get_search_service()
            doc_results = await search_service.enhanced_search(
                query.question, 
                query.search_type, 
                query.max_results, 
                current_user.organization_id
            )
            
            # Process documentation results
            for doc in doc_results:
                if hasattr(doc, 'payload'):
                    # Qdrant ScoredPoint object
                    all_sources.append({
                        "type": "documentation",
                        "title": doc.payload.get("title", "Unknown Document"),
                        "content": doc.payload.get("content", "")[:500],
                        "score": doc.score if hasattr(doc, 'score') else 0.0,
                        "metadata": {
                            "source": "qdrant",
                            "collection": "docs"
                        }
                    })
                else:
                    # Dict object
                    all_sources.append({
                        "type": "documentation",
                        "title": doc.get("title", "Unknown Document"),
                        "content": doc.get("content", "")[:500],
                        "score": doc.get("score", 0.0),
                        "metadata": {
                            "source": "database"
                        }
                    })
                    
        except Exception as e:
            print(f"Error searching docs: {e}")
        
        # Search Jira tickets semantically
        try:
            qdrant_indexer = await get_qdrant_indexer()
            if qdrant_indexer:
                jira_tickets = await qdrant_indexer.search_jira_tickets(
                    query.question,
                    current_user.organization_id,
                    limit=min(query.max_results, 5)
                )
                print(f"🔍 Found {len(jira_tickets)} Jira tickets (semantic)")
            else:
                # Fallback to PostgreSQL exact search
                jira_tickets = await db_service.search_jira_tickets(
                    query.question,
                    current_user.organization_id,
                    limit=min(query.max_results, 5)
                )
                print(f"Found {len(jira_tickets)} Jira tickets (exact)")
            
            # Process Jira results
            for ticket in jira_tickets:
                all_sources.append({
                    "type": "jira_ticket",
                    "title": f"{ticket.get('ticket_key', 'Unknown')}: {ticket.get('summary', 'No summary')}",
                    "content": ticket.get('description', '')[:500],
                    "score": ticket.get('score', 0.0),
                    "metadata": {
                        "ticket_key": ticket.get('ticket_key'),
                        "status": ticket.get('status'),
                        "priority": ticket.get('priority'),
                        "assignee": ticket.get('assignee'),
                        "created_date": ticket.get('created_date')
                    }
                })
                
        except Exception as e:
            print(f"Error searching Jira tickets: {e}")
        
        # Search commits semantically
        try:
            qdrant_indexer = await get_qdrant_indexer()
            if qdrant_indexer:
                commit_results = await qdrant_indexer.search_commits(
                    query.question,
                    current_user.organization_id,
                    limit=min(query.max_results, 5)
                )
                print(f"🔍 Found {len(commit_results)} commits (semantic)")
            else:
                commit_results = []
            
            # Process commit results
            for commit in commit_results:
                all_sources.append({
                    "type": "commit",
                    "title": f"Commit: {commit.get('message', 'No message')[:50]}",
                    "content": f"SHA: {commit.get('sha', 'unknown')[:7]}\nMessage: {commit.get('message', '')}",
                    "score": commit.get('score', 0.0),
                    "metadata": {
                        "sha": commit.get('sha'),
                        "author": commit.get('author_name'),
                        "commit_date": commit.get('commit_date'),
                        "files_changed": commit.get('files_changed', [])
                    }
                })
                
        except Exception as e:
            print(f"Error searching commits: {e}")
        
        # Search code files semantically
        try:
            qdrant_indexer = await get_qdrant_indexer()
            if qdrant_indexer:
                code_files = await qdrant_indexer.search_code_files(
                    query.question,
                    current_user.organization_id,
                    limit=min(query.max_results, 5)
                )
                print(f"🔍 Found {len(code_files)} code files (semantic)")
            else:
                # Fallback to PostgreSQL exact search
                code_files = await db_service.search_code_files(
                    query.question,
                    current_user.organization_id,
                    limit=min(query.max_results, 5)
                )
            
            # Process code file results
            for file in code_files:
                all_sources.append({
                    "type": "code_file",
                    "title": f"File: {file.get('file_path', 'Unknown file')}",
                    "content": file.get('content', '')[:500],
                    "score": file.get('score', 0.0),
                    "metadata": {
                        "file_path": file.get('file_path'),
                        "language": file.get('language'),
                        "size": file.get('size'),
                        "last_modified": file.get('last_modified')
                    }
                })
                
        except Exception as e:
            print(f"Error searching code files: {e}")
        
        # Sort by relevance score and limit results
        all_sources.sort(key=lambda x: x.get('score', 0.0), reverse=True)
        top_sources = all_sources[:query.max_results]
        
        return top_sources, context_history
    
    def build_context_from_sources(
        self, 
        sources: List[Dict[str, Any]], 
        context_history: str,
        max_context_length: int = 4000
    ) -> str:
        """
        Build AI context from search results with intelligent truncation.
        
        Args:
            sources: Search results
            context_history: Previous conversation context
            max_context_length: Maximum context length in characters
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0
        
        # Add conversation history if available
        if context_history:
            history_part = f"Previous conversation:\n{context_history}\n\n"
            if current_length + len(history_part) < max_context_length:
                context_parts.append(history_part)
                current_length += len(history_part)
        
        # Add search results
        if sources:
            context_parts.append("Relevant information found:\n")
            current_length += len("Relevant information found:\n")
            
            for i, source in enumerate(sources, 1):
                # Format source information
                source_text = f"{i}. [{source['type']}] {source['title']}\n"
                source_text += f"   {source['content']}\n"
                
                # Add metadata if available
                if source.get('metadata'):
                    metadata = source['metadata']
                    if source['type'] == 'jira_ticket':
                        source_text += f"   Status: {metadata.get('status', 'Unknown')}, Priority: {metadata.get('priority', 'Unknown')}\n"
                    elif source['type'] == 'commit':
                        source_text += f"   Author: {metadata.get('author', 'Unknown')}, SHA: {metadata.get('sha', 'Unknown')[:7]}\n"
                    elif source['type'] == 'code_file':
                        source_text += f"   Language: {metadata.get('language', 'Unknown')}, Path: {metadata.get('file_path', 'Unknown')}\n"
                
                source_text += "\n"
                
                # Check if adding this source would exceed the limit
                if current_length + len(source_text) > max_context_length:
                    context_parts.append(f"... (truncated {len(sources) - i + 1} additional sources due to length limit)\n")
                    break
                
                context_parts.append(source_text)
                current_length += len(source_text)
        
        return "".join(context_parts)
    
    def create_enhanced_prompt(
        self, 
        query: Query, 
        context: str
    ) -> str:
        """
        Create an enhanced prompt with proper context and instructions.
        
        Args:
            query: User query
            context: Built context from search results
            
        Returns:
            Formatted prompt for AI generation
        """
        prompt = f"""You are an AI assistant helping developers understand their codebase and project information. Based on the following context, please answer the user's question comprehensively and accurately.

Context:
{context}

Question: {query.question}

Instructions:
1. Provide a helpful and detailed answer based on the available information
2. Reference specific sources when possible (e.g., "According to ticket PROJ-123..." or "In the file auth.py...")
3. If the context doesn't contain enough information to fully answer the question, say so and suggest what additional information might be needed
4. Be concise but thorough
5. Use technical language appropriate for developers

Answer:"""
        
        return prompt
    
    async def generate_streaming_response(
        self, 
        query: Query, 
        current_user: User
    ) -> AsyncGenerator[str, None]:
        """
        Generate complete streaming response with comprehensive error handling and termination.
        
        Args:
            query: User query
            current_user: Authenticated user
            
        Yields:
            Formatted SSE events
        """
        builder = StreamingResponseBuilder()
        start_time = time.time()
        sources = []
        context_history = ""
        full_response = ""
        chunk_count = 0
        
        try:
            # Perform comprehensive search with error handling
            try:
                sources, context_history = await self.perform_comprehensive_search(query, current_user)
                logger.info(f"Search completed: {len(sources)} sources found")
            except Exception as search_error:
                logger.error(f"Search failed: {search_error}")
                yield await builder.send_error(
                    error_type="search_failed",
                    message="Failed to search data sources. Continuing with limited context.",
                    recoverable=True,
                    error_code="SEARCH_ERROR"
                )
                # Continue with empty sources
                sources = []
                context_history = ""
            
            # Send metadata event
            sources_searched = {
                "documentation": len([s for s in sources if s['type'] == 'documentation']),
                "jira_tickets": len([s for s in sources if s['type'] == 'jira_ticket']),
                "commits": len([s for s in sources if s['type'] == 'commit']),
                "code_files": len([s for s in sources if s['type'] == 'code_file'])
            }
            
            try:
                yield await builder.send_metadata(
                    sources_searched=sources_searched,
                    total_results=len(sources)
                )
            except Exception as metadata_error:
                logger.error(f"Failed to send metadata: {metadata_error}")
                yield await builder.send_error(
                    error_type="metadata_error",
                    message="Failed to send search metadata",
                    recoverable=True,
                    error_code="METADATA_ERROR"
                )
            
            # Send sources event with error handling
            try:
                yield await builder.send_sources(sources)
            except Exception as sources_error:
                logger.error(f"Failed to send sources: {sources_error}")
                yield await builder.send_error(
                    error_type="sources_error",
                    message="Failed to send source information",
                    recoverable=True,
                    error_code="SOURCES_ERROR"
                )
            
            # Build context and generate AI response with error handling
            try:
                context = self.build_context_from_sources(sources, context_history)
                prompt = self.create_enhanced_prompt(query, context)
                
                # Get AI service and generate context-aware streaming response
                ai_service = await get_ai_service()
                
                # Use the enhanced context-aware streaming method with timeout
                async with asyncio.timeout(120):  # 2 minute timeout
                    async for chunk in ai_service.generate_context_aware_streaming_response(
                        question=query.question,
                        search_results=sources,
                        conversation_history=context_history,
                        model=query.model or "mistral",
                        temperature=0.7,
                        role="software_architect"
                    ):
                        full_response += chunk
                        chunk_count += 1
                        
                        try:
                            yield await builder.send_content_chunk(
                                chunk=chunk,
                                chunk_id=chunk_count
                            )
                        except Exception as chunk_error:
                            logger.error(f"Failed to send chunk {chunk_count}: {chunk_error}")
                            # Continue with next chunk
                            continue
                            
            except asyncio.TimeoutError:
                logger.error("AI response generation timed out")
                yield await builder.send_error(
                    error_type="ai_timeout",
                    message="AI response generation timed out. Please try a shorter query.",
                    recoverable=True,
                    error_code="AI_TIMEOUT"
                )
                return
                
            except Exception as ai_error:
                logger.error(f"AI generation failed: {ai_error}")
                
                # Try fallback response
                try:
                    fallback_response = f"""I apologize, but I encountered an issue generating a response to your question: "{query.question}"

Based on the search results I found ({len(sources)} sources), I can see there is relevant information available, but I'm having trouble processing it right now.

Please try:
1. Rephrasing your question
2. Making your query more specific
3. Trying again in a moment

The search found information from:
{', '.join([f"{count} {source_type}" for source_type, count in sources_searched.items() if count > 0])}"""

                    yield await builder.send_content_chunk(
                        chunk=fallback_response,
                        chunk_id=1
                    )
                    full_response = fallback_response
                    chunk_count = 1
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback response failed: {fallback_error}")
                    yield await builder.send_error(
                        error_type="ai_failed",
                        message="AI service is currently unavailable. Please try again later.",
                        recoverable=True,
                        error_code="AI_SERVICE_ERROR"
                    )
                    return
            
            # Collect comprehensive metadata with error handling
            try:
                processing_time = time.time() - start_time
                
                # Calculate token counts using AI service
                ai_service = await get_ai_service()
                total_tokens = ai_service.count_tokens(full_response) if full_response else 0
                prompt_tokens = ai_service.count_tokens(context) if context else 0
                
                # Collect source relevance scores
                source_scores = [s.get('score', 0.0) for s in sources]
                avg_relevance = sum(source_scores) / len(source_scores) if source_scores else 0.0
                
                # Build comprehensive query metadata
                query_metadata = {
                    "question": query.question,
                    "search_type": query.search_type,
                    "model": query.model or "mistral",
                    "sources_found": sources_searched,
                    "chunks_sent": chunk_count,
                    "context_length": len(context) if context else 0,
                    "response_length": len(full_response),
                    "processing_time": processing_time,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": max(0, total_tokens - prompt_tokens),
                    "average_source_relevance": avg_relevance,
                    "max_source_relevance": max(source_scores) if source_scores else 0.0,
                    "min_source_relevance": min(source_scores) if source_scores else 0.0,
                    "streaming_performance": {
                        "chunks_per_second": chunk_count / processing_time if processing_time > 0 else 0,
                        "characters_per_second": len(full_response) / processing_time if processing_time > 0 else 0,
                        "tokens_per_second": total_tokens / processing_time if processing_time > 0 else 0
                    },
                    "error_recovery": {
                        "search_errors": len(sources) == 0,
                        "ai_fallback_used": "fallback" in full_response.lower(),
                        "partial_response": chunk_count < 5
                    }
                }
                
                yield await builder.send_completion(
                    total_tokens=total_tokens,
                    model_used=query.model,
                    query_metadata=query_metadata
                )
                
            except Exception as completion_error:
                logger.error(f"Failed to send completion: {completion_error}")
                yield await builder.send_error(
                    error_type="completion_error",
                    message="Failed to finalize response",
                    recoverable=False,
                    error_code="COMPLETION_ERROR"
                )
            
            # Update conversation history with error handling
            try:
                if query.session_id and full_response:
                    self.conversation_service.add_message(
                        query.session_id, 
                        query.question, 
                        full_response, 
                        sources
                    )
            except Exception as history_error:
                logger.warning(f"Failed to update conversation history: {history_error}")
                # Don't fail the entire request for history errors
            
        except asyncio.CancelledError:
            # Handle client disconnection gracefully
            logger.info("Client disconnected during streaming")
            try:
                yield await builder.send_error(
                    error_type="connection_cancelled",
                    message="Client disconnected during streaming",
                    recoverable=False,
                    error_code="CLIENT_DISCONNECT"
                )
            except:
                # If we can't send the error, the connection is already closed
                pass
            
        except Exception as e:
            # Use comprehensive error handling with fallback
            logger.error(f"Unexpected streaming error: {e}")
            try:
                async for error_chunk in create_error_response(
                    error=e,
                    query=query.question,
                    fallback_handler=lambda: self._create_non_streaming_fallback(query, current_user)
                ):
                    yield error_chunk
            except Exception as fallback_error:
                logger.error(f"Error handling fallback failed: {fallback_error}")
                # Last resort error message
                try:
                    yield await builder.send_error(
                        error_type="critical_error",
                        message="A critical error occurred. Please refresh and try again.",
                        recoverable=False,
                        error_code="CRITICAL_ERROR"
                    )
                except:
                    # If even this fails, there's nothing more we can do
                    pass
    
    async def estimate_response_time(
        self, 
        query: Query, 
        current_user: User
    ) -> Dict[str, Any]:
        """
        Estimate streaming response time and provide progress information.
        
        Args:
            query: User query
            current_user: Authenticated user
            
        Returns:
            Estimation metadata
        """
        # Base estimation factors
        query_complexity = len(query.question.split())
        max_results = query.max_results or 5
        
        # Estimate search time (0.1s per result + base 0.5s)
        search_time = 0.5 + (max_results * 0.1)
        
        # Estimate AI generation time based on model and complexity
        model_factors = {
            "mistral": 1.0,
            "llama2": 1.2,
            "codellama": 1.1
        }
        
        generation_time = (query_complexity / 10) * model_factors.get(query.model or "mistral", 1.0)
        
        total_estimated_time = search_time + generation_time
        
        return {
            "estimated_duration": total_estimated_time,
            "search_time": search_time,
            "generation_time": generation_time,
            "query_complexity": query_complexity,
            "max_results": max_results,
            "model": query.model or "mistral"
        }
    
    async def collect_streaming_metrics(
        self,
        query: Query,
        sources: List[Dict[str, Any]],
        response_chunks: List[str],
        processing_time: float,
        ai_service
    ) -> Dict[str, Any]:
        """
        Collect comprehensive streaming metrics for analysis and optimization.
        
        Args:
            query: Original query
            sources: Search results
            response_chunks: List of response chunks
            processing_time: Total processing time
            ai_service: AI service instance for token counting
            
        Returns:
            Comprehensive metrics dictionary
        """
        full_response = "".join(response_chunks)
        
        # Basic metrics
        metrics = {
            "query_id": getattr(query, 'query_id', None),
            "timestamp": time.time(),
            "processing_time": processing_time,
            "total_chunks": len(response_chunks),
            "response_length": len(full_response),
            "model_used": query.model or "mistral"
        }
        
        # Token metrics
        if ai_service:
            metrics.update({
                "total_tokens": ai_service.count_tokens(full_response),
                "average_tokens_per_chunk": ai_service.count_tokens(full_response) / len(response_chunks) if response_chunks else 0
            })
        
        # Source metrics
        if sources:
            source_types = {}
            source_scores = []
            
            for source in sources:
                source_type = source.get('type', 'unknown')
                source_types[source_type] = source_types.get(source_type, 0) + 1
                
                score = source.get('score', 0.0)
                if score > 0:
                    source_scores.append(score)
            
            metrics.update({
                "sources_by_type": source_types,
                "total_sources": len(sources),
                "average_source_relevance": sum(source_scores) / len(source_scores) if source_scores else 0.0,
                "max_source_relevance": max(source_scores) if source_scores else 0.0,
                "relevance_distribution": {
                    "high": len([s for s in source_scores if s > 0.8]),
                    "medium": len([s for s in source_scores if 0.5 <= s <= 0.8]),
                    "low": len([s for s in source_scores if s < 0.5])
                }
            })
        
        # Performance metrics
        if processing_time > 0:
            metrics.update({
                "chunks_per_second": len(response_chunks) / processing_time,
                "characters_per_second": len(full_response) / processing_time,
                "tokens_per_second": metrics.get("total_tokens", 0) / processing_time
            })
        
        # Chunk analysis
        if response_chunks:
            chunk_lengths = [len(chunk) for chunk in response_chunks]
            metrics.update({
                "chunk_statistics": {
                    "average_length": sum(chunk_lengths) / len(chunk_lengths),
                    "max_length": max(chunk_lengths),
                    "min_length": min(chunk_lengths),
                    "length_variance": self._calculate_variance(chunk_lengths)
                }
            })
        
        # Query complexity metrics
        query_words = len(query.question.split())
        metrics.update({
            "query_complexity": {
                "word_count": query_words,
                "character_count": len(query.question),
                "complexity_score": min(1.0, query_words / 20)  # Normalize to 0-1
            }
        })
        
        return metrics
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    async def track_search_processing_time(
        self,
        query: Query,
        current_user: User
    ) -> Dict[str, float]:
        """
        Track processing time for each search component.
        
        Args:
            query: User query
            current_user: Authenticated user
            
        Returns:
            Dictionary with timing for each search component
        """
        timings = {}
        
        # Time documentation search
        start_time = time.time()
        try:
            search_service = await get_search_service()
            await search_service.enhanced_search(
                query.question, 
                query.search_type, 
                query.max_results, 
                current_user.organization_id
            )
            timings["documentation_search"] = time.time() - start_time
        except Exception:
            timings["documentation_search"] = time.time() - start_time
        
        # Time Jira search
        start_time = time.time()
        try:
            qdrant_indexer = await get_qdrant_indexer()
            if qdrant_indexer:
                await qdrant_indexer.search_jira_tickets(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
            timings["jira_search"] = time.time() - start_time
        except Exception:
            timings["jira_search"] = time.time() - start_time
        
        # Time commit search
        start_time = time.time()
        try:
            qdrant_indexer = await get_qdrant_indexer()
            if qdrant_indexer:
                await qdrant_indexer.search_commits(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
            timings["commit_search"] = time.time() - start_time
        except Exception:
            timings["commit_search"] = time.time() - start_time
        
        # Time code file search
        start_time = time.time()
        try:
            qdrant_indexer = await get_qdrant_indexer()
            if qdrant_indexer:
                await qdrant_indexer.search_code_files(
                    query.question,
                    current_user.organization_id,
                    limit=3
                )
            timings["code_search"] = time.time() - start_time
        except Exception:
            timings["code_search"] = time.time() - start_time
        
        return timings
    
    async def _create_non_streaming_fallback(
        self,
        query: Query,
        current_user: User
    ) -> AsyncGenerator[str, None]:
        """
        Create a non-streaming fallback response when streaming fails.
        
        Args:
            query: Original query
            current_user: Authenticated user
            
        Yields:
            Fallback response chunks
        """
        try:
            # Perform basic search without streaming
            sources, context_history = await self.perform_comprehensive_search(query, current_user)
            
            # Build context
            context = self.build_context_from_sources(sources, context_history)
            
            # Get AI service and generate non-streaming response
            ai_service = await get_ai_service()
            
            # Create a simpler prompt for fallback
            prompt = f"""Based on the available information, please answer this question: {query.question}

Available context:
{context[:1000]}  # Limit context for fallback

Please provide a helpful answer based on the information above."""

            # Generate non-streaming response
            response = await ai_service.generate_response(prompt, query.model or "mistral")
            
            # Convert to streaming format
            if isinstance(response, str):
                # Split response into chunks for pseudo-streaming
                words = response.split()
                chunk_size = 8
                
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i + chunk_size]) + " "
                    yield StreamingEventFormatter.format_content_event(chunk)
                    await asyncio.sleep(0.05)  # Small delay for natural feel
            else:
                # Handle AIResponse object
                content = response.get("content", "") if isinstance(response, dict) else str(response)
                words = content.split()
                chunk_size = 8
                
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i + chunk_size]) + " "
                    yield StreamingEventFormatter.format_content_event(chunk)
                    await asyncio.sleep(0.05)
                    
        except Exception as fallback_error:
            # If fallback also fails, provide a basic error message
            error_message = f"""I apologize, but I'm experiencing technical difficulties right now. 

Your question was: "{query.question}"

Please try:
1. Refreshing the page and asking again
2. Simplifying your question
3. Checking your internet connection
4. Contacting support if the issue persists

Thank you for your patience."""

            words = error_message.split()
            chunk_size = 6
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size]) + " "
                yield StreamingEventFormatter.format_content_event(chunk)
                await asyncio.sleep(0.1)