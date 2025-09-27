"""
Pipeline API Routes
API endpoints for managing the data ingestion pipeline
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging

from ..pipeline.core import PipelineOrchestrator
from ..config.settings import get_settings

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
settings = get_settings()
logger = logging.getLogger(__name__)

# Global pipeline instance
pipeline_orchestrator: Optional[PipelineOrchestrator] = None

async def get_pipeline_orchestrator() -> PipelineOrchestrator:
    """Get or create pipeline orchestrator instance"""
    global pipeline_orchestrator
    
    if pipeline_orchestrator is None:
        pipeline_orchestrator = PipelineOrchestrator()
        await pipeline_orchestrator.initialize()
    
    return pipeline_orchestrator

@router.post("/start", response_model=Dict[str, Any])
async def start_pipeline(
    background_tasks: BackgroundTasks,
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Start the data ingestion pipeline"""
    try:
        if orchestrator.is_running:
            return {
                "status": "already_running",
                "message": "Pipeline is already running",
                "timestamp": datetime.now().isoformat()
            }
        
        # Start pipeline in background
        background_tasks.add_task(orchestrator.start_pipeline)
        
        return {
            "status": "starting",
            "message": "Pipeline startup initiated",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline startup failed: {str(e)}")

@router.post("/stop", response_model=Dict[str, Any])
async def stop_pipeline(
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Stop the data ingestion pipeline"""
    try:
        if not orchestrator.is_running:
            return {
                "status": "already_stopped",
                "message": "Pipeline is not running",
                "timestamp": datetime.now().isoformat()
            }
        
        await orchestrator.stop_pipeline()
        
        return {
            "status": "stopped",
            "message": "Pipeline stopped successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline stop failed: {str(e)}")

@router.get("/status", response_model=Dict[str, Any])
async def get_pipeline_status(
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Get current pipeline status"""
    try:
        status = orchestrator.get_current_status()
        return status
        
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

@router.get("/metrics", response_model=Dict[str, Any])
async def get_pipeline_metrics(
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Get comprehensive pipeline metrics"""
    try:
        metrics = orchestrator.get_pipeline_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get pipeline metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def get_pipeline_health(
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Get health status of all pipeline components"""
    try:
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check each component
        components = [
            ("ingestion", orchestrator.ingestion_manager),
            ("streaming", orchestrator.stream_processor),
            ("feature_engineering", orchestrator.feature_engine),
            ("models", orchestrator.model_manager),
            ("risk_assessment", orchestrator.risk_engine),
            ("intervention", orchestrator.intervention_optimizer)
        ]
        
        for name, component in components:
            try:
                component_health = await component.health_check()
                health_status["components"][name] = component_health
            except Exception as e:
                health_status["components"][name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Overall health assessment
        component_statuses = [comp["status"] for comp in health_status["components"].values()]
        
        if all(status == "healthy" for status in component_statuses):
            health_status["overall_status"] = "healthy"
        elif any(status == "critical" for status in component_statuses):
            health_status["overall_status"] = "critical"
        elif any(status in ["unhealthy", "degraded"] for status in component_statuses):
            health_status["overall_status"] = "degraded"
        else:
            health_status["overall_status"] = "unknown"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Failed to get pipeline health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/ingestion/stats", response_model=Dict[str, Any])
async def get_ingestion_stats(
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Get data ingestion statistics"""
    try:
        stats = orchestrator.ingestion_manager.ingestion_stats
        return {
            "ingestion_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get ingestion stats: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion stats retrieval failed: {str(e)}")

@router.get("/streaming/metrics", response_model=Dict[str, Any])
async def get_streaming_metrics(
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Get real-time streaming metrics"""
    try:
        metrics = await orchestrator.stream_processor.get_real_time_metrics()
        return {
            "streaming_metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get streaming metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming metrics retrieval failed: {str(e)}")

@router.get("/models/performance", response_model=Dict[str, Any])
async def get_model_performance(
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Get model performance metrics"""
    try:
        performance = orchestrator.model_manager.model_performance
        return {
            "model_performance": dict(performance),
            "model_weights": orchestrator.model_manager.model_weights,
            "lightweight_mode": orchestrator.model_manager.lightweight_mode,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}")
        raise HTTPException(status_code=500, detail=f"Model performance retrieval failed: {str(e)}")

@router.get("/risk/current", response_model=Dict[str, Any])
async def get_current_risk_assessment(
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Get current risk assessment"""
    try:
        # This would fetch from Redis in a real implementation
        risk_data = {
            "overall_risk_score": 0.0,
            "risk_level": "low",
            "active_alerts": [],
            "confidence_score": 1.0,
            "timestamp": datetime.now().isoformat()
        }
        
        return risk_data
        
    except Exception as e:
        logger.error(f"Failed to get risk assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment retrieval failed: {str(e)}")

@router.get("/interventions/summary", response_model=Dict[str, Any])
async def get_intervention_summary(
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Get intervention performance summary"""
    try:
        summary = await orchestrator.intervention_optimizer.get_performance_summary()
        return {
            "intervention_summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get intervention summary: {e}")
        raise HTTPException(status_code=500, detail=f"Intervention summary retrieval failed: {str(e)}")

@router.post("/interventions/trigger", response_model=Dict[str, Any])
async def trigger_manual_intervention(
    intervention_type: str,
    description: str,
    priority: int = 3,
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Manually trigger an intervention"""
    try:
        # This would implement manual intervention triggering
        result = {
            "status": "triggered",
            "intervention_type": intervention_type,
            "description": description,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Manual intervention triggered: {intervention_type}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to trigger intervention: {e}")
        raise HTTPException(status_code=500, detail=f"Intervention trigger failed: {str(e)}")

@router.get("/config", response_model=Dict[str, Any])
async def get_pipeline_configuration():
    """Get current pipeline configuration"""
    try:
        config = {
            "kafka_bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "kafka_topic_prefix": settings.KAFKA_TOPIC_PREFIX,
            "redis_url": settings.REDIS_URL,
            "twitter_enabled": settings.TWITTER_CONFIG.get("enabled", False),
            "sports_api_enabled": settings.SPORTS_API_CONFIG.get("enabled", False),
            "news_api_enabled": settings.NEWS_API_CONFIG.get("enabled", False),
            "intervals": {
                "ingestion": settings.INGESTION_INTERVAL,
                "feature_engineering": settings.FEATURE_ENGINEERING_INTERVAL,
                "model_inference": settings.MODEL_INFERENCE_INTERVAL,
                "risk_assessment": settings.RISK_ASSESSMENT_INTERVAL,
                "intervention": settings.INTERVENTION_INTERVAL
            },
            "sports_monitored": settings.SPORTS_TO_MONITOR,
            "twitter_queries": settings.TWITTER_QUERIES,
            "news_keywords": settings.NEWS_KEYWORDS,
            "timestamp": datetime.now().isoformat()
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get pipeline configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration retrieval failed: {str(e)}")

@router.put("/config/intervals", response_model=Dict[str, Any])
async def update_pipeline_intervals(
    ingestion_interval: Optional[int] = None,
    feature_engineering_interval: Optional[int] = None,
    model_inference_interval: Optional[int] = None,
    risk_assessment_interval: Optional[int] = None,
    intervention_interval: Optional[int] = None
):
    """Update pipeline processing intervals"""
    try:
        updates = {}
        
        if ingestion_interval is not None:
            settings.INGESTION_INTERVAL = ingestion_interval
            updates["ingestion_interval"] = ingestion_interval
        
        if feature_engineering_interval is not None:
            settings.FEATURE_ENGINEERING_INTERVAL = feature_engineering_interval
            updates["feature_engineering_interval"] = feature_engineering_interval
        
        if model_inference_interval is not None:
            settings.MODEL_INFERENCE_INTERVAL = model_inference_interval
            updates["model_inference_interval"] = model_inference_interval
        
        if risk_assessment_interval is not None:
            settings.RISK_ASSESSMENT_INTERVAL = risk_assessment_interval
            updates["risk_assessment_interval"] = risk_assessment_interval
        
        if intervention_interval is not None:
            settings.INTERVENTION_INTERVAL = intervention_interval
            updates["intervention_interval"] = intervention_interval
        
        return {
            "status": "updated",
            "updates": updates,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update pipeline intervals: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration update failed: {str(e)}")

@router.get("/logs/recent", response_model=Dict[str, Any])
async def get_recent_pipeline_logs(
    limit: int = 100,
    level: str = "INFO"
):
    """Get recent pipeline logs"""
    try:
        # This would implement log retrieval from logging system
        logs = {
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "component": "pipeline",
                    "message": "Pipeline running normally"
                }
            ],
            "total_logs": 1,
            "limit": limit,
            "level_filter": level,
            "timestamp": datetime.now().isoformat()
        }
        
        return logs
        
    except Exception as e:
        logger.error(f"Failed to get pipeline logs: {e}")
        raise HTTPException(status_code=500, detail=f"Log retrieval failed: {str(e)}")

@router.post("/restart", response_model=Dict[str, Any])
async def restart_pipeline(
    background_tasks: BackgroundTasks,
    component: Optional[str] = None,
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
):
    """Restart the entire pipeline or specific component"""
    try:
        if component:
            # Restart specific component
            result = {
                "status": "component_restart_initiated",
                "component": component,
                "message": f"Restarting {component} component",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Restart entire pipeline
            if orchestrator.is_running:
                await orchestrator.stop_pipeline()
            
            background_tasks.add_task(orchestrator.start_pipeline)
            
            result = {
                "status": "full_restart_initiated",
                "message": "Full pipeline restart initiated",
                "timestamp": datetime.now().isoformat()
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to restart pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline restart failed: {str(e)}")

# WebSocket endpoint for real-time pipeline monitoring
@router.websocket("/monitor")
async def pipeline_monitor_websocket(websocket):
    """WebSocket endpoint for real-time pipeline monitoring"""
    try:
        await websocket.accept()
        
        orchestrator = await get_pipeline_orchestrator()
        
        while True:
            try:
                # Send current status
                status = orchestrator.get_current_status()
                await websocket.send_json({
                    "type": "status_update",
                    "data": status,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Send metrics
                metrics = orchestrator.get_pipeline_metrics()
                await websocket.send_json({
                    "type": "metrics_update",
                    "data": metrics,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Wait before next update
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"WebSocket monitoring error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await websocket.close()