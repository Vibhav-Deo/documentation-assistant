"""
Unified AI Service

Combines the functionality of ai.py and ai_enhanced.py into a single,
comprehensive service with feature flags for backward compatibility.

Features:
- Basic AI response generation (from ai.py)
- Streaming responses with SSE (from ai_enhanced.py)
- Multi-model support with fallback (from ai_enhanced.py)
- Advanced prompt engineering (from ai_enhanced.py)
- Context window management (from ai_enhanced.py)
- Response metadata tracking (from ai_enhanced.py)
- Multi-source context building (from ai.py)
- Clickable link injection (from ai.py)

This service extends BaseService for consistent error handling and logging.
"""

import json
import requests
import time
from typing import AsyncGenerator, List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from fastapi import HTTPException
from config import OLLAMA_API_URL
import tiktoken
import logging

from services.shared.base_service import BaseService
from services.infrastructure.database.base_repository import BaseRepository

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Structured AI response with metadata."""
    content: str
    model_used: str
    tokens_consumed: int
    prompt_tokens: int
    completion_tokens: int
    confidence_score: float
    processing_time_ms: int
    fallback_used: bool
    context_truncated: bool
    metadata: Dict[str, Any]


class UnifiedAIService(BaseService):
    """
    Unified AI service combining basic and enhanced capabilities.
    
    Provides both simple and advanced AI operations with feature flags
    for backward compatibility and progressive enhancement.
    """
    
    def __init__(self, repository: BaseRepository, api_url: str = OLLAMA_API_URL):
        super().__init__(repository)
        
        # Configuration
        self.api_url = api_url
        self.models = ["mistral", "llama2", "codellama"]  # Priority order
        self.max_tokens = {
            "mistral": 8192,
            "llama2": 4096,
            "codellama": 16384
        }
        
        # System prompts for different use cases
        self.system_prompts = {
            "default": "You are a helpful AI assistant.",
            "technical": "You are a technical documentation expert.",
            "support": "You are a customer support specialist.",
            "software_architect": "You are an experienced software architect with deep knowledge of system design, scalability, and best practices.",
            "security_expert": "You are a cybersecurity expert specializing in application security, threat modeling, and secure coding practices.",
            "technical_writer": "You are a technical writer skilled at explaining complex concepts clearly and concisely.",
            "code_reviewer": "You are a senior code reviewer focused on code quality, maintainability, and best practices."
        }
        
        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            self.tokenizer = None
            logger.warning("Failed to initialize tokenizer, using fallback token counting")
    
    # ========================================
    # BASIC AI OPERATIONS (from ai.py)
    # ========================================
    
    async def generate_response(
        self, 
        prompt: str, 
        model: str = "mistral", 
        temperature: float = 0.7,
        enhanced: bool = False
    ) -> Union[str, AIResponse]:
        """
        Generate AI response using Ollama.
        
        Args:
            prompt: Input prompt
            model: Model to use (mistral, llama2, codellama)
            temperature: Sampling temperature (0.0-1.0)
            enhanced: If True, returns AIResponse with metadata
            
        Returns:
            String response (basic) or AIResponse (enhanced)
        """
        operation_name = f"generate_response_{model}"
        
        if enhanced:
            return await self.handle_operation(
                operation_name,
                self._generate_enhanced_response,
                prompt, model, temperature
            )
        else:
            return await self.handle_operation(
                operation_name,
                self._generate_basic_response,
                prompt, model, temperature
            )
    
    async def _generate_basic_response(
        self, 
        prompt: str, 
        model: str, 
        temperature: float
    ) -> str:
        """Generate basic AI response (original ai.py functionality)."""
        try:
            # Optimized settings for mistral (7B)
            options = {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "num_ctx": self.max_tokens.get(model, 8192),
                "num_predict": 2048
            }
            
            payload = {
                "model": model, 
                "prompt": prompt,
                "options": options
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            answer_parts = []
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            answer_parts.append(data["response"])
                    except json.JSONDecodeError:
                        continue
            
            return "".join(answer_parts).strip()
            
        except (requests.ConnectionError, requests.Timeout) as e:
            raise HTTPException(status_code=503, detail=f"Ollama service unavailable: {str(e)}")
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Ollama API error: {str(e)}")
    
    async def _generate_enhanced_response(
        self, 
        prompt: str, 
        model: str, 
        temperature: float
    ) -> AIResponse:
        """Generate enhanced AI response with metadata."""
        start_time = time.time()
        
        try:
            content = await self._generate_basic_response(prompt, model, temperature)
            
            # Calculate metrics
            processing_time = int((time.time() - start_time) * 1000)
            prompt_tokens = self._count_tokens(prompt)
            completion_tokens = self._count_tokens(content)
            total_tokens = prompt_tokens + completion_tokens
            
            return AIResponse(
                content=content,
                model_used=model,
                tokens_consumed=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                confidence_score=0.9,  # High confidence for primary model
                processing_time_ms=processing_time,
                fallback_used=False,
                context_truncated=False,
                metadata={
                    "temperature": temperature,
                    "model_available": True
                }
            )
            
        except Exception as e:
            # Return error response
            processing_time = int((time.time() - start_time) * 1000)
            return AIResponse(
                content=f"Error generating response: {str(e)}",
                model_used=model,
                tokens_consumed=0,
                prompt_tokens=0,
                completion_tokens=0,
                confidence_score=0.0,
                processing_time_ms=processing_time,
                fallback_used=False,
                context_truncated=False,
                metadata={
                    "error": str(e),
                    "temperature": temperature
                }
            )
    
    # ========================================
    # STREAMING OPERATIONS (from ai_enhanced.py)
    # ========================================
    
    async def generate_streaming_response(
        self,
        prompt: str,
        model: str = "mistral",
        temperature: float = 0.7,
        search_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming AI response using Server-Sent Events with optional search context.
        
        Args:
            prompt: Input prompt
            model: Model to use (mistral, llama2, codellama)
            temperature: Sampling temperature (0.0-1.0)
            search_context: Optional search context metadata for enhanced responses
            
        Yields:
            Chunks of the response as they're generated
            
        Validates: Requirements 10.1
        """
        try:
            # Enhance prompt with search context if provided
            enhanced_prompt = self._enhance_prompt_with_context(prompt, search_context)
            
            # Calculate optimal context window based on prompt length
            context_window = self._calculate_optimal_context_window(enhanced_prompt, model)
            
            options = {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "num_ctx": context_window,
                "num_predict": min(2048, context_window // 2)  # Reserve space for response
            }
            
            payload = {
                "model": model,
                "prompt": enhanced_prompt,
                "options": options,
                "stream": True
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            yield data["response"]
                        
                        # Check if done
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except (requests.ConnectionError, requests.Timeout) as e:
            raise HTTPException(
                status_code=503,
                detail=f"Streaming service unavailable: {str(e)}"
            )
        except requests.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"Streaming error: {str(e)}"
            )
    
    async def generate_context_aware_streaming_response(
        self,
        question: str,
        search_results: List[Dict[str, Any]],
        conversation_history: Optional[str] = None,
        model: str = "mistral",
        temperature: float = 0.7,
        role: str = "software_architect"
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response with full search context integration.
        
        Args:
            question: User's question
            search_results: List of search results from various sources
            conversation_history: Previous conversation context
            model: AI model to use
            temperature: Sampling temperature
            role: System role for prompt engineering
            
        Yields:
            Chunks of the AI response
        """
        # Build comprehensive context
        context = self._build_comprehensive_context(
            search_results, 
            conversation_history,
            max_length=self.max_tokens.get(model, 8192) // 2
        )
        
        # Create role-specific prompt
        system_prompt = self.system_prompts.get(role, self.system_prompts["default"])
        
        # Build the full prompt
        prompt = f"""{system_prompt}

Context Information:
{context}

User Question: {question}

Please provide a comprehensive answer based on the context above. Reference specific sources when possible and be precise about technical details.

Answer:"""
        
        # Generate streaming response with context metadata
        search_context = {
            "sources_count": len(search_results),
            "has_conversation_history": bool(conversation_history),
            "context_length": len(context),
            "role": role
        }
        
        async for chunk in self.generate_streaming_response(
            prompt=prompt,
            model=model,
            temperature=temperature,
            search_context=search_context
        ):
            yield chunk
    
    def _enhance_prompt_with_context(
        self, 
        prompt: str, 
        search_context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Enhance prompt with search context metadata for better responses.
        
        Args:
            prompt: Original prompt
            search_context: Search context metadata
            
        Returns:
            Enhanced prompt
        """
        if not search_context:
            return prompt
        
        # Add context hints to improve response quality
        context_hints = []
        
        if search_context.get("sources_count", 0) > 0:
            context_hints.append(f"Drawing from {search_context['sources_count']} relevant sources")
        
        if search_context.get("has_conversation_history"):
            context_hints.append("Considering previous conversation context")
        
        if search_context.get("role"):
            context_hints.append(f"Responding as a {search_context['role']}")
        
        if context_hints:
            hint_text = " | ".join(context_hints)
            return f"[Context: {hint_text}]\n\n{prompt}"
        
        return prompt
    
    def _calculate_optimal_context_window(self, prompt: str, model: str) -> int:
        """
        Calculate optimal context window based on prompt length and model capabilities.
        
        Args:
            prompt: The full prompt
            model: AI model being used
            
        Returns:
            Optimal context window size
        """
        max_context = self.max_tokens.get(model, 8192)
        
        # Estimate token count
        if self.tokenizer:
            try:
                prompt_tokens = len(self.tokenizer.encode(prompt))
            except:
                # Fallback estimation
                prompt_tokens = len(prompt.split()) * 1.3
        else:
            # Rough estimation: 1 token ≈ 0.75 words
            prompt_tokens = len(prompt.split()) * 1.3
        
        # Reserve space for response (at least 512 tokens)
        response_tokens = max(512, max_context // 4)
        
        # Calculate optimal window
        optimal_window = min(max_context, int(prompt_tokens + response_tokens))
        
        return optimal_window
    
    def _build_comprehensive_context(
        self,
        search_results: List[Dict[str, Any]],
        conversation_history: Optional[str] = None,
        max_length: int = 4000
    ) -> str:
        """
        Build comprehensive context from search results with intelligent prioritization.
        
        Args:
            search_results: Search results from various sources
            conversation_history: Previous conversation
            max_length: Maximum context length
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0
        
        # Add conversation history first (if available and not too long)
        if conversation_history and len(conversation_history) < max_length // 3:
            history_part = f"Previous Conversation:\n{conversation_history}\n\n"
            context_parts.append(history_part)
            current_length += len(history_part)
        
        # Sort search results by score and type priority
        type_priority = {
            "jira_ticket": 1,
            "code_file": 2,
            "commit": 3,
            "documentation": 4
        }
        
        sorted_results = sorted(
            search_results,
            key=lambda x: (type_priority.get(x.get('type', 'unknown'), 5), -x.get('score', 0))
        )
        
        # Add search results with intelligent truncation
        context_parts.append("Relevant Information:\n")
        current_length += len("Relevant Information:\n")
        
        for i, result in enumerate(sorted_results, 1):
            # Format result based on type
            result_text = self._format_search_result(result, i)
            
            # Check if adding this result would exceed the limit
            if current_length + len(result_text) > max_length:
                remaining_count = len(sorted_results) - i + 1
                if remaining_count > 0:
                    context_parts.append(f"\n... ({remaining_count} additional sources available but truncated for brevity)\n")
                break
            
            context_parts.append(result_text)
            current_length += len(result_text)
        
        return "".join(context_parts)
    
    def _format_search_result(self, result: Dict[str, Any], index: int) -> str:
        """
        Format a search result for context inclusion.
        
        Args:
            result: Search result dictionary
            index: Result index
            
        Returns:
            Formatted result string
        """
        result_type = result.get('type', 'unknown')
        title = result.get('title', 'Unknown')
        content = result.get('content', '')[:300]  # Limit content length
        metadata = result.get('metadata', {})
        
        formatted = f"\n{index}. [{result_type.upper()}] {title}\n"
        formatted += f"   Content: {content}\n"
        
        # Add type-specific metadata
        if result_type == 'jira_ticket' and metadata:
            formatted += f"   Status: {metadata.get('status', 'Unknown')}"
            formatted += f" | Priority: {metadata.get('priority', 'Unknown')}"
            if metadata.get('assignee'):
                formatted += f" | Assignee: {metadata.get('assignee')}"
            formatted += "\n"
            
        elif result_type == 'commit' and metadata:
            formatted += f"   Author: {metadata.get('author', 'Unknown')}"
            formatted += f" | SHA: {metadata.get('sha', 'Unknown')[:7]}"
            if metadata.get('commit_date'):
                formatted += f" | Date: {metadata.get('commit_date')}"
            formatted += "\n"
            
        elif result_type == 'code_file' and metadata:
            formatted += f"   Path: {metadata.get('file_path', 'Unknown')}"
            formatted += f" | Language: {metadata.get('language', 'Unknown')}"
            if metadata.get('size'):
                formatted += f" | Size: {metadata.get('size')} bytes"
            formatted += "\n"
        
        return formatted
    
    # ========================================
    # ENHANCED STREAMING METHODS
    # ========================================
    
    async def generate_streaming_response_with_metadata(
        self,
        prompt: str,
        model: str = "mistral",
        temperature: float = 0.7,
        search_context: Optional[Dict[str, Any]] = None,
        track_tokens: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming response with detailed metadata tracking.
        
        Args:
            prompt: Input prompt
            model: AI model to use
            temperature: Sampling temperature
            search_context: Search context metadata
            track_tokens: Whether to track token usage
            
        Yields:
            Dictionaries containing chunk data and metadata
        """
        start_time = time.time()
        total_tokens = 0
        chunk_count = 0
        
        try:
            async for chunk in self.generate_streaming_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                search_context=search_context
            ):
                chunk_count += 1
                
                # Estimate tokens in this chunk
                if track_tokens and self.tokenizer:
                    try:
                        chunk_tokens = len(self.tokenizer.encode(chunk))
                    except:
                        chunk_tokens = len(chunk.split()) * 1.3
                else:
                    chunk_tokens = len(chunk.split()) * 1.3
                
                total_tokens += chunk_tokens
                
                yield {
                    "chunk": chunk,
                    "chunk_id": chunk_count,
                    "chunk_tokens": int(chunk_tokens),
                    "total_tokens": int(total_tokens),
                    "processing_time": time.time() - start_time,
                    "model": model,
                    "temperature": temperature
                }
                
        except Exception as e:
            yield {
                "error": str(e),
                "chunk_id": chunk_count,
                "total_tokens": int(total_tokens),
                "processing_time": time.time() - start_time,
                "model": model
            }
    
    async def stream_with_progress_tracking(
        self,
        prompt: str,
        model: str = "mistral",
        temperature: float = 0.7,
        estimated_length: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming response with progress tracking.
        
        Args:
            prompt: Input prompt
            model: AI model to use
            temperature: Sampling temperature
            estimated_length: Estimated response length for progress calculation
            
        Yields:
            Dictionaries with chunk data and progress information
        """
        start_time = time.time()
        total_chars = 0
        chunk_count = 0
        
        # Estimate response length if not provided
        if estimated_length is None:
            estimated_length = len(prompt.split()) * 2  # Rough estimate
        
        async for chunk in self.generate_streaming_response(
            prompt=prompt,
            model=model,
            temperature=temperature
        ):
            chunk_count += 1
            total_chars += len(chunk)
            
            # Calculate progress
            progress = min(1.0, total_chars / estimated_length) if estimated_length > 0 else 0.0
            
            yield {
                "chunk": chunk,
                "chunk_id": chunk_count,
                "total_characters": total_chars,
                "progress": progress,
                "estimated_completion": estimated_length,
                "processing_time": time.time() - start_time,
                "chunks_per_second": chunk_count / (time.time() - start_time) if time.time() > start_time else 0
            }
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the configured tokenizer.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except:
                pass
        
        # Fallback estimation
        return int(len(text.split()) * 1.3)
    
    def estimate_streaming_duration(
        self,
        prompt: str,
        model: str = "mistral",
        search_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate streaming response duration and characteristics.
        
        Args:
            prompt: Input prompt
            model: AI model to use
            search_context: Optional search context
            
        Returns:
            Estimation metadata
        """
        # Count prompt tokens
        prompt_tokens = self.count_tokens(prompt)
        
        # Model-specific generation speeds (tokens per second)
        model_speeds = {
            "mistral": 25,
            "llama2": 20,
            "codellama": 22
        }
        
        speed = model_speeds.get(model, 20)
        
        # Estimate response length based on prompt complexity
        estimated_response_tokens = min(
            prompt_tokens * 0.8,  # Response usually shorter than prompt
            self.max_tokens.get(model, 8192) // 4  # Reserve context space
        )
        
        # Calculate estimated duration
        estimated_duration = estimated_response_tokens / speed
        
        # Add overhead for search context processing
        if search_context and search_context.get("sources_count", 0) > 0:
            context_overhead = search_context["sources_count"] * 0.1
            estimated_duration += context_overhead
        
        return {
            "estimated_duration_seconds": estimated_duration,
            "prompt_tokens": prompt_tokens,
            "estimated_response_tokens": int(estimated_response_tokens),
            "model_speed_tokens_per_second": speed,
            "model": model,
            "has_search_context": bool(search_context),
            "context_sources": search_context.get("sources_count", 0) if search_context else 0
        }
    
    async def validate_streaming_capability(self, model: str = "mistral") -> Dict[str, Any]:
        """
        Validate that streaming is working properly with the specified model.
        
        Args:
            model: Model to test
            
        Returns:
            Validation results
        """
        test_prompt = "Hello, this is a streaming test."
        start_time = time.time()
        chunks_received = 0
        total_content = ""
        
        try:
            async for chunk in self.generate_streaming_response(
                prompt=test_prompt,
                model=model,
                temperature=0.1
            ):
                chunks_received += 1
                total_content += chunk
                
                # Limit test to prevent long responses
                if chunks_received >= 10 or len(total_content) > 100:
                    break
            
            duration = time.time() - start_time
            
            return {
                "streaming_available": True,
                "model": model,
                "test_duration": duration,
                "chunks_received": chunks_received,
                "content_length": len(total_content),
                "average_chunk_size": len(total_content) / chunks_received if chunks_received > 0 else 0,
                "chunks_per_second": chunks_received / duration if duration > 0 else 0
            }
            
        except Exception as e:
            return {
                "streaming_available": False,
                "model": model,
                "error": str(e),
                "test_duration": time.time() - start_time
            }
    
    def get_streaming_metrics(self) -> Dict[str, Any]:
        """
        Get current streaming performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return {
            "supported_models": self.models,
            "max_tokens_per_model": self.max_tokens,
            "api_url": self.api_url,
            "tokenizer_available": self.tokenizer is not None,
            "system_prompts_available": list(self.system_prompts.keys())
        }
    
    # ========================================
    # MULTI-MODEL FALLBACK (from ai_enhanced.py)
    # ========================================
    
    async def generate_with_fallback(
        self,
        prompt: str,
        models: Optional[List[str]] = None,
        temperature: float = 0.7
    ) -> AIResponse:
        """
        Generate response with automatic fallback to alternative models.
        
        Tries models in priority order until one succeeds.
        
        Args:
            prompt: Input prompt
            models: List of models to try (defaults to all available)
            temperature: Sampling temperature
            
        Returns:
            AIResponse with content and metadata
            
        Validates: Requirements 10.2
        """
        if models is None:
            models = self.models
        
        start_time = time.time()
        fallback_used = False
        last_error = None
        
        for i, model in enumerate(models):
            try:
                if i > 0:
                    fallback_used = True
                    logger.info(f"Falling back to model: {model}")
                
                # Generate response
                content = await self._generate_basic_response(prompt, model, temperature)
                
                # Calculate metrics
                processing_time = int((time.time() - start_time) * 1000)
                prompt_tokens = self._count_tokens(prompt)
                completion_tokens = self._count_tokens(content)
                total_tokens = prompt_tokens + completion_tokens
                
                # Estimate confidence (higher for primary model, lower for fallbacks)
                confidence = 0.9 if i == 0 else max(0.5, 0.9 - (i * 0.2))
                
                return AIResponse(
                    content=content,
                    model_used=model,
                    tokens_consumed=total_tokens,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    confidence_score=confidence,
                    processing_time_ms=processing_time,
                    fallback_used=fallback_used,
                    context_truncated=False,
                    metadata={
                        "models_tried": i + 1,
                        "temperature": temperature
                    }
                )
                
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model} failed: {str(e)}")
                continue
        
        # All models failed
        raise HTTPException(
            status_code=503,
            detail=f"All AI models failed. Last error: {str(last_error)}"
        )
    
    # ========================================
    # PROMPT ENGINEERING (from ai_enhanced.py)
    # ========================================
    
    def build_prompt(self, question: str, context: str = "", context_history: str = "") -> str:
        """Build enhanced prompt for AI model (original ai.py functionality)."""
        prompt_parts = [
            "You are a helpful AI assistant specialized in providing accurate, well-structured answers."
        ]
        
        if context_history:
            prompt_parts.append(f"\nPrevious conversation context:\n{context_history}")
        
        if context:
            prompt_parts.extend([
                "\nInstructions:",
                "- Answer based ONLY on the provided context",
                "- Be specific and cite relevant information",
                "- If the context doesn't contain the answer, say so clearly",
                "- Structure your response with clear sections if needed",
                "- Use bullet points or numbered lists for clarity when appropriate",
                f"\nContext:\n{context}",
                f"\nQuestion: {question}",
                "\nAnswer:"
            ])
        else:
            prompt_parts.extend([
                "\nInstructions:",
                "- Provide accurate, helpful information",
                "- Be concise but comprehensive",
                "- Structure your response clearly",
                "- If you're uncertain, acknowledge limitations",
                f"\nQuestion: {question}",
                "\nAnswer:"
            ])
        
        return "\n".join(prompt_parts)
    
    def build_few_shot_prompt(
        self,
        question: str,
        examples: List[Dict[str, str]],
        context: str = ""
    ) -> str:
        """
        Build prompt with few-shot learning examples.
        
        Few-shot learning improves accuracy by showing the model examples
        of the desired input-output format.
        
        Args:
            question: The actual question to answer
            examples: List of {"question": "...", "answer": "..."} examples
            context: Optional context information
            
        Returns:
            Formatted prompt with examples
            
        Validates: Requirements 10.3
        """
        prompt_parts = [
            "You are an expert assistant. Learn from these examples:\n"
        ]
        
        # Add examples
        for i, example in enumerate(examples, 1):
            prompt_parts.append(f"\nExample {i}:")
            prompt_parts.append(f"Question: {example['question']}")
            prompt_parts.append(f"Answer: {example['answer']}\n")
        
        # Add context if provided
        if context:
            prompt_parts.append(f"\nContext:\n{context}\n")
        
        # Add actual question
        prompt_parts.append(f"\nNow answer this question:")
        prompt_parts.append(f"Question: {question}")
        prompt_parts.append("Answer:")
        
        return "\n".join(prompt_parts)
    
    def build_chain_of_thought_prompt(
        self,
        question: str,
        context: str = ""
    ) -> str:
        """
        Build prompt encouraging step-by-step reasoning.
        
        Chain-of-thought prompting improves reasoning by asking the model
        to think through the problem step by step.
        
        Args:
            question: The question to answer
            context: Optional context information
            
        Returns:
            Formatted prompt encouraging reasoning
            
        Validates: Requirements 10.3
        """
        prompt_parts = [
            "You are an expert assistant. Think through this problem step by step.\n"
        ]
        
        if context:
            prompt_parts.append(f"Context:\n{context}\n")
        
        prompt_parts.extend([
            f"\nQuestion: {question}\n",
            "Let's approach this systematically:",
            "1. First, identify the key information",
            "2. Then, analyze what's being asked",
            "3. Consider relevant factors",
            "4. Finally, provide a clear answer\n",
            "Step-by-step reasoning:"
        ])
        
        return "\n".join(prompt_parts)
    
    def build_role_based_prompt(
        self,
        question: str,
        role: str,
        context: str = ""
    ) -> str:
        """
        Build prompt with specific role/persona.
        
        Args:
            question: The question to answer
            role: Role to adopt (e.g., "software_architect", "security_expert")
            context: Optional context
            
        Returns:
            Formatted prompt with role
            
        Validates: Requirements 10.3
        """
        role_prompt = self.system_prompts.get(role, f"You are an expert {role}.")
        
        prompt_parts = [role_prompt]
        
        if context:
            prompt_parts.append(f"\nContext:\n{context}")
        
        prompt_parts.extend([
            f"\nQuestion: {question}",
            "\nProvide a detailed, expert-level answer:"
        ])
        
        return "\n".join(prompt_parts)
    
    def build_contextual_prompt(
        self, 
        question: str, 
        context: str = "", 
        context_history: str = "", 
        prompt_type: str = "default"
    ) -> str:
        """Build prompt with system context for specific use cases."""
        system_prompt = self.system_prompts.get(prompt_type, self.system_prompts["default"])
        base_prompt = self.build_prompt(question, context, context_history)
        return f"{system_prompt}\n\n{base_prompt}"
    
    # ========================================
    # CONTEXT WINDOW MANAGEMENT (from ai_enhanced.py)
    # ========================================
    
    async def manage_context_window(
        self,
        context: str,
        max_tokens: int = 8192,
        strategy: str = "truncate"
    ) -> tuple[str, bool]:
        """
        Intelligently manage context to fit within token limits.
        
        Strategies:
        - truncate: Keep first N tokens
        - summarize: Use AI to summarize (not implemented yet)
        - smart_truncate: Keep beginning and end, remove middle
        
        Args:
            context: The context text
            max_tokens: Maximum tokens allowed
            strategy: Management strategy
            
        Returns:
            Tuple of (managed_context, was_truncated)
            
        Validates: Requirements 10.4
        """
        current_tokens = self._count_tokens(context)
        
        if current_tokens <= max_tokens:
            return context, False
        
        # Reserve some tokens for the prompt structure
        available_tokens = int(max_tokens * 0.8)
        
        if strategy == "truncate":
            # Simple truncation - keep first N tokens
            truncated = self._truncate_to_tokens(context, available_tokens)
            return truncated, True
        
        elif strategy == "smart_truncate":
            # Keep beginning and end, remove middle
            beginning_tokens = int(available_tokens * 0.6)
            end_tokens = int(available_tokens * 0.4)
            
            beginning = self._truncate_to_tokens(context, beginning_tokens)
            
            # Get end portion
            words = context.split()
            end_start = max(0, len(words) - end_tokens)
            end = " ".join(words[end_start:])
            
            managed = f"{beginning}\n\n[... content truncated ...]\n\n{end}"
            return managed, True
        
        else:
            # Default to simple truncation
            truncated = self._truncate_to_tokens(context, available_tokens)
            return truncated, True
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except:
                pass
        
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximately max_tokens."""
        if self.tokenizer:
            try:
                tokens = self.tokenizer.encode(text)
                if len(tokens) <= max_tokens:
                    return text
                truncated_tokens = tokens[:max_tokens]
                return self.tokenizer.decode(truncated_tokens)
            except:
                pass
        
        # Fallback: character-based truncation
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."
    
    # ========================================
    # MULTI-SOURCE CONTEXT BUILDING (from ai.py)
    # ========================================
    
    def build_multi_source_context(
        self,
        confluence_results: List[Dict],
        jira_results: List[Dict],
        commit_results: List[Dict],
        code_results: List[Dict]
    ) -> str:
        """
        Build comprehensive context from all sources for AI query.
        ENHANCED: Larger context window for mistral model.
        """
        context_parts = []

        # Add Confluence documentation (3 results, 500 chars)
        if confluence_results:
            context_parts.append("=== DOCUMENTATION (Confluence) ===")
            for i, doc in enumerate(confluence_results[:3], 1):
                title = doc.get('title', 'Untitled')
                text = doc.get('text', '')[:500]
                context_parts.append(f"\n[DOC-{i}] {title}")
                context_parts.append(f"{text}...")

        # Add Jira tickets (3 results, 400 chars)
        if jira_results:
            context_parts.append("\n\n=== JIRA TICKETS ===")
            for i, ticket in enumerate(jira_results[:3], 1):
                key = ticket.get('ticket_key', 'N/A')
                summary = ticket.get('summary', 'No summary')
                status = ticket.get('status', 'Unknown')
                priority = ticket.get('priority', 'N/A')
                description = ticket.get('description', '')[:400]
                url = ticket.get('url', '')

                if url:
                    context_parts.append(f"\n[TICKET-{i}] [{key}: {summary}]({url})")
                else:
                    context_parts.append(f"\n[TICKET-{i}] {key}: {summary}")

                context_parts.append(f"Status: {status}")
                if description:
                    context_parts.append(f"Description: {description}...")

        # Add Git commits (3 results, 300 chars)
        if commit_results:
            context_parts.append("\n\n=== GIT COMMITS ===")
            for i, commit in enumerate(commit_results[:3], 1):
                sha = commit.get('short_sha') or (commit.get('sha') or 'N/A')[:7]
                message = commit.get('message', 'No message')[:300]
                author = commit.get('author_name', 'Unknown')
                files = commit.get('files_changed', [])[:5]
                url = commit.get('url', '')

                if url:
                    context_parts.append(f"\n[COMMIT-{i}] [{sha}]({url}) by {author}")
                else:
                    context_parts.append(f"\n[COMMIT-{i}] {sha} by {author}")

                context_parts.append(f"Message: {message}")
                if files:
                    context_parts.append(f"Files: {', '.join(files)}")

        # Add Code files (3 results)
        if code_results:
            context_parts.append("\n\n=== CODE FILES ===")
            for i, file in enumerate(code_results[:3], 1):
                path = file.get('file_path', 'Unknown')
                language = file.get('language', 'N/A')
                functions = file.get('functions', [])[:5]
                classes = file.get('classes', [])[:5]
                url = file.get('url', '')

                if url:
                    context_parts.append(f"\n[CODE-{i}] [{path}]({url}) ({language})")
                else:
                    context_parts.append(f"\n[CODE-{i}] {path} ({language})")

                if functions:
                    context_parts.append(f"Functions: {', '.join(functions)}")
                if classes:
                    context_parts.append(f"Classes: {', '.join(classes)}")

        return "\n".join(context_parts) if context_parts else ""
    
    def build_multi_source_prompt(
        self,
        question: str,
        confluence_results: List[Dict],
        jira_results: List[Dict],
        commit_results: List[Dict],
        code_results: List[Dict]
    ) -> str:
        """
        Build enhanced prompt for multi-source AI query.
        ENHANCED: Chain-of-thought reasoning and confidence scoring for mistral.
        """
        context = self.build_multi_source_context(
            confluence_results,
            jira_results,
            commit_results,
            code_results
        )

        # Count results from each source
        sources_found = []
        if confluence_results:
            sources_found.append(f"{len(confluence_results)} documentation pages")
        if jira_results:
            sources_found.append(f"{len(jira_results)} Jira tickets")
        if commit_results:
            sources_found.append(f"{len(commit_results)} commits")
        if code_results:
            sources_found.append(f"{len(code_results)} code files")

        sources_summary = ", ".join(sources_found) if sources_found else "no results"

        # Few-shot example for better accuracy
        few_shot_example = """Example:
Question: "How does authentication work?"
Thinking:
1. Documentation shows JWT-based auth in [DOC-1]
2. Implementation ticket is [TICKET-1: DEMO-001]
3. Code is in [CODE-1] auth.py with login() function
4. Recent fix in [COMMIT-1] improved token validation

Answer: The system uses JWT authentication as documented in [DOC-1]. This was implemented in [TICKET-1: DEMO-001] with code in [CODE-1] auth.py. The login() function generates tokens, and [COMMIT-1] recently improved validation.
"""

        prompt = f"""You are an expert development assistant with access to multiple information sources.

I found {sources_summary} related to the query.

{few_shot_example}

Instructions:
1. Think step-by-step:
   - What does the documentation say?
   - What tickets are related?
   - What code implements this?
   - How do these sources connect?

2. Provide your answer:
   - Reference sources using their IDs ([DOC-1], [TICKET-2], [COMMIT-3], [CODE-4])
   - Preserve EXACT markdown links from context like [[DEMO-001: Title](url)]
   - Explain connections between sources
   - Structure clearly with sections if needed
   - Be specific and actionable

3. For each source you reference, indicate confidence:
   - HIGH: Direct answer in source
   - MEDIUM: Inferred from source
   - LOW: Tangentially related

Context from multiple sources:
{context}

Question: {question}

Thinking (step-by-step analysis):

Answer (with source references and confidence levels):"""

        return prompt
    
    def inject_clickable_links(
        self,
        answer: str,
        confluence_results: List[Dict],
        jira_results: List[Dict],
        commit_results: List[Dict],
        code_results: List[Dict]
    ) -> str:
        """
        Post-process AI answer to inject clickable markdown links for source references.

        Replaces plain text like [TICKET-1] with clickable links like [[DEMO-001](url)].
        This ensures clickable links work even if the AI doesn't preserve them.
        """
        import re

        # Build lookup maps for URLs
        # Confluence docs
        doc_map = {}
        for i, doc in enumerate(confluence_results[:3], 1):
            title = doc.get('title', 'Untitled')[:50]
            # Try to get URL from metadata or page_url field
            url = doc.get('url', '') or doc.get('page_url', '') or doc.get('metadata', {}).get('url', '')
            if url:
                doc_map[f"[DOC-{i}]"] = f"[[DOC-{i}: {title}]({url})]"

        # Jira tickets
        jira_map = {}
        for i, ticket in enumerate(jira_results[:3], 1):
            key = ticket.get('ticket_key', 'N/A')
            url = ticket.get('url', '')
            summary = ticket.get('summary', '')[:50]
            if url:
                jira_map[f"[TICKET-{i}]"] = f"[[TICKET-{i}: {key}]({url})]"

        commit_map = {}
        for i, commit in enumerate(commit_results[:3], 1):
            sha = commit.get('short_sha') or (commit.get('sha') or 'N/A')[:7]
            url = commit.get('url', '')
            if url:
                commit_map[f"[COMMIT-{i}]"] = f"[[COMMIT-{i}: {sha}]({url})]"

        code_map = {}
        for i, file in enumerate(code_results[:3], 1):
            path = file.get('file_path', 'Unknown')
            url = file.get('url', '')
            if url:
                # Extract filename for cleaner display
                filename = path.split('/')[-1]
                code_map[f"[CODE-{i}]"] = f"[[CODE-{i}: {filename}]({url})]"

        # Replace references with clickable links
        for ref, link in doc_map.items():
            answer = answer.replace(ref, link)

        for ref, link in jira_map.items():
            answer = answer.replace(ref, link)

        for ref, link in commit_map.items():
            answer = answer.replace(ref, link)

        for ref, link in code_map.items():
            answer = answer.replace(ref, link)

        return answer
    
    # ========================================
    # METADATA AND UTILITIES
    # ========================================
    
    def get_response_metadata(self, response: AIResponse) -> Dict[str, Any]:
        """
        Extract metadata from AI response for tracking and analysis.
        
        Validates: Requirements 10.5
        """
        return {
            "model_used": response.model_used,
            "tokens_consumed": response.tokens_consumed,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "confidence_score": response.confidence_score,
            "processing_time_ms": response.processing_time_ms,
            "fallback_used": response.fallback_used,
            "context_truncated": response.context_truncated,
            **response.metadata
        }
    
    def get_system_prompt(self, prompt_type: str = "default") -> str:
        """Get system prompt based on use case."""
        return self.system_prompts.get(prompt_type, self.system_prompts["default"])
    
    # ========================================
    # BACKWARD COMPATIBILITY METHODS
    # ========================================
    
    # These methods maintain compatibility with existing code that uses ai.py
    
    async def generate_basic_response(self, prompt: str, model: str = "mistral", temperature: float = 0.7) -> str:
        """Backward compatibility method for basic response generation."""
        return await self.generate_response(prompt, model, temperature, enhanced=False)
    
    async def generate_enhanced_response(self, prompt: str, model: str = "mistral", temperature: float = 0.7) -> AIResponse:
        """Backward compatibility method for enhanced response generation."""
        return await self.generate_response(prompt, model, temperature, enhanced=True)


# ========================================
# FACTORY FUNCTION FOR EASY MIGRATION
# ========================================

def create_ai_service(repository: BaseRepository, enhanced: bool = True) -> UnifiedAIService:
    """
    Factory function to create AI service instance.
    
    Args:
        repository: Database repository instance
        enhanced: Whether to enable enhanced features by default
        
    Returns:
        UnifiedAIService instance
    """
    service = UnifiedAIService(repository)
    service._enhanced_by_default = enhanced
    return service