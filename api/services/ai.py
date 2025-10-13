import json
import requests
from typing import Dict, List, Optional
from fastapi import HTTPException
from config import OLLAMA_API_URL

class AIService:
    def __init__(self):
        self.api_url = OLLAMA_API_URL
        self.system_prompts = {
            "default": "You are a helpful AI assistant.",
            "technical": "You are a technical documentation expert.",
            "support": "You are a customer support specialist."
        }
    
    def generate_response(self, prompt: str, model: str = "mistral", temperature: float = 0.7) -> str:
        """Generate AI response using Ollama"""
        try:
            payload = {
                "model": model, 
                "prompt": prompt,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            r = requests.post(
                self.api_url,
                json=payload,
                stream=True,
                timeout=60
            )
            r.raise_for_status()
            
            answer_parts = []
            for line in r.iter_lines():
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
    
    def build_prompt(self, question: str, context: str = "", context_history: str = "") -> str:
        """Build enhanced prompt for AI model"""
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
    
    def get_system_prompt(self, prompt_type: str = "default") -> str:
        """Get system prompt based on use case"""
        return self.system_prompts.get(prompt_type, self.system_prompts["default"])
    
    def build_contextual_prompt(self, question: str, context: str = "", context_history: str = "", prompt_type: str = "default") -> str:
        """Build prompt with system context for specific use cases"""
        system_prompt = self.get_system_prompt(prompt_type)
        base_prompt = self.build_prompt(question, context, context_history)
        return f"{system_prompt}\n\n{base_prompt}"

    def build_multi_source_context(
        self,
        confluence_results: List[Dict],
        jira_results: List[Dict],
        commit_results: List[Dict],
        code_results: List[Dict]
    ) -> str:
        """
        Build comprehensive context from all sources for AI query.

        This is the CORE USP: combining Confluence docs, Jira tickets, Git commits,
        and code files into one unified context for the AI.
        """
        context_parts = []

        # Add Confluence documentation
        if confluence_results:
            context_parts.append("=== DOCUMENTATION (Confluence) ===")
            for i, doc in enumerate(confluence_results[:3], 1):  # Top 3
                title = doc.get('title', 'Untitled')
                text = doc.get('text', '')[:500]  # Limit length
                context_parts.append(f"\n[DOC-{i}] {title}")
                context_parts.append(f"{text}...")

        # Add Jira tickets
        if jira_results:
            context_parts.append("\n\n=== JIRA TICKETS ===")
            for i, ticket in enumerate(jira_results[:3], 1):  # Top 3
                key = ticket.get('ticket_key', 'N/A')
                summary = ticket.get('summary', 'No summary')
                status = ticket.get('status', 'Unknown')
                description = ticket.get('description', '')[:300]
                url = ticket.get('url', '')

                # Create clickable link if URL is available
                if url:
                    context_parts.append(f"\n[TICKET-{i}] [{key}: {summary}]({url})")
                else:
                    context_parts.append(f"\n[TICKET-{i}] {key}: {summary}")

                context_parts.append(f"Status: {status}")
                if description:
                    context_parts.append(f"Description: {description}...")

        # Add Git commits
        if commit_results:
            context_parts.append("\n\n=== GIT COMMITS ===")
            for i, commit in enumerate(commit_results[:3], 1):  # Top 3
                sha = commit.get('short_sha') or (commit.get('sha') or 'N/A')[:7]
                message = commit.get('message', 'No message')[:200]
                author = commit.get('author_name', 'Unknown')
                files = commit.get('files_changed', [])[:5]
                url = commit.get('url', '')

                # Create clickable link if URL is available
                if url:
                    context_parts.append(f"\n[COMMIT-{i}] [{sha}]({url}) by {author}")
                else:
                    context_parts.append(f"\n[COMMIT-{i}] {sha} by {author}")

                context_parts.append(f"Message: {message}")
                if files:
                    context_parts.append(f"Files changed: {', '.join(files)}")

        # Add Code files
        if code_results:
            context_parts.append("\n\n=== CODE FILES ===")
            for i, file in enumerate(code_results[:3], 1):  # Top 3
                path = file.get('file_path', 'Unknown')
                language = file.get('language', 'N/A')
                functions = file.get('functions', [])[:5]
                classes = file.get('classes', [])[:5]
                url = file.get('url', '')

                # Create clickable link if URL is available
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

        CORE USP: User asks about a feature/bug/enhancement, AI searches ALL sources
        and provides comprehensive answer showing Confluence docs, Jira tickets,
        commits, and code files.
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

        prompt = f"""You are an intelligent development assistant with access to multiple information sources.

I found {sources_summary} related to the query.

Instructions:
- Provide a comprehensive answer based on ALL the sources provided
- The context includes CLICKABLE MARKDOWN LINKS for tickets, commits, and code files
- When referencing sources, use the EXACT markdown link format from the context (e.g., [TICKET-1], [COMMIT-2], [CODE-3])
- If the source has a clickable link in the context like [[DEMO-001: Title](url)], preserve that link in your response
- Explain HOW the information connects across sources
- If a Jira ticket relates to commits or code, make that connection explicit
- Structure your answer clearly with sections if needed
- Be specific and actionable

Context from multiple sources:
{context}

Question: {question}

Answer (reference sources using their IDs and preserve markdown links):"""

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