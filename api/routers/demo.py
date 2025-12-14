"""
Demo Router

Handles demo-specific endpoints for investor presentations and demonstrations.
"""

import time
from fastapi import APIRouter, HTTPException, Depends
from models import User
from services.shared.auth import get_current_user
from services.infrastructure.database import db_service

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/")
async def demo_dashboard():
    """
    Demo dashboard endpoint - returns demo page info.
    """
    from services.shared.response_formatter import ResponseFormatter
    
    return ResponseFormatter.success(
        data={
            "title": "Investor Demo Dashboard",
            "version": "2.0.0",
            "features": [
                "AI-powered semantic search",
                "Predictive analytics",
                "Auto-tagging and classification",
                "Decision extraction and analysis",
                "Real-time streaming responses"
            ],
            "metrics": {
                "documents_indexed": 1250,
                "queries_processed": 3420,
                "ai_insights_generated": 890,
                "accuracy_score": 0.94
            }
        },
        message="Demo dashboard data retrieved successfully"
    )

@router.post("/generate-data")
async def generate_demo_data(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Generate comprehensive demo data for investor presentations.
    
    Request body:
    {
        "org_name": "Demo Corporation" (optional)
    }
    
    Returns:
    - Summary of generated data including counts and relationships
    - Gap examples for demonstration
    - Generation time and metadata
    
    Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5
    """
    try:
        from dependencies.container import get_demo_data_generator
        demo_data_generator = await get_demo_data_generator()
        
        if not demo_data_generator:
            raise HTTPException(status_code=503, detail="DemoDataGenerator not initialized")
        
        org_name = request.get("org_name", "Demo Corporation")
        
        # Progress tracking for real-time updates
        progress_updates = []
        
        def progress_callback(message: str, percentage: int):
            progress_updates.append({
                "message": message,
                "percentage": percentage,
                "timestamp": time.time()
            })
        
        # Generate demo data
        result = await demo_data_generator.generate_complete_demo_data(
            org_name=org_name,
            progress_callback=progress_callback
        )
        
        # Add progress updates to result
        result["progress_updates"] = progress_updates
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo data generation failed: {str(e)}")


@router.get("/status")
async def get_demo_status(current_user: User = Depends(get_current_user)):
    """
    Get status of demo data in the system.
    
    Returns:
    - Whether demo data exists
    - Summary of demo organization data
    - Last generation timestamp
    
    Validates: Requirements 11.5
    """
    try:
        # Check if demo organization exists
        async with db_service.pool.acquire() as conn:
            demo_org = await conn.fetchrow("""
                SELECT id, name, created_at 
                FROM organizations 
                WHERE name ILIKE '%demo%' 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            if not demo_org:
                return {
                    "status": "no_demo_data",
                    "message": "No demo data found. Use /api/demo/generate-data to create demo data."
                }
            
            org_id = str(demo_org["id"])
            
            # Get counts of demo data
            ticket_count = await conn.fetchval(
                "SELECT COUNT(*) FROM jira_tickets WHERE organization_id = $1", org_id
            )
            commit_count = await conn.fetchval(
                "SELECT COUNT(*) FROM commits WHERE organization_id = $1", org_id
            )
            pr_count = await conn.fetchval(
                "SELECT COUNT(*) FROM pull_requests WHERE organization_id = $1", org_id
            )
            file_count = await conn.fetchval(
                "SELECT COUNT(*) FROM code_files WHERE organization_id = $1", org_id
            )
            
            return {
                "status": "demo_data_exists",
                "organization": {
                    "id": org_id,
                    "name": demo_org["name"],
                    "created_at": demo_org["created_at"].isoformat()
                },
                "data_summary": {
                    "tickets": ticket_count,
                    "commits": commit_count,
                    "pull_requests": pr_count,
                    "code_files": file_count
                }
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get demo status: {str(e)}")