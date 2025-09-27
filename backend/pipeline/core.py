"""
Core Pipeline Orchestrator
Manages the entire data-to-action pipeline as described in the BTP paper
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from dataclasses import dataclass, asdict

from config.settings import settings
from .ingestion import DataIngestionManager
from .streaming import StreamProcessor
from .feature_engineering import FeatureEngineeringEngine
from .models import EnsembleModelManager
from .risk_assessment import RiskAssessmentEngine
from .intervention import InterventionOptimizer

# settings imported above
logger = logging.getLogger(__name__)

@dataclass
class PipelineStatus:
    """Pipeline status tracking"""
    stage: str
    status: str
    timestamp: datetime
    metrics: Dict[str, Any]
    error: Optional[str] = None

class PipelineOrchestrator:
    """
    Main orchestrator for the modular data ingestion pipeline
    Implements the high-level architecture from BTP paper
    """
    
    def __init__(self):
        self.ingestion_manager = DataIngestionManager()
        self.stream_processor = StreamProcessor()
        self.feature_engine = FeatureEngineeringEngine()
        self.model_manager = EnsembleModelManager()
        self.risk_engine = RiskAssessmentEngine()
        self.intervention_optimizer = InterventionOptimizer()
        
        self.pipeline_status: List[PipelineStatus] = []
        self.is_running = False
        
    async def initialize(self):
        """Initialize all pipeline components"""
        try:
            logger.info("Initializing pipeline components...")
            
            # Initialize components in order
            await self.ingestion_manager.initialize()
            await self.stream_processor.initialize()
            await self.feature_engine.initialize()
            await self.model_manager.initialize()
            await self.risk_engine.initialize()
            await self.intervention_optimizer.initialize()
            
            self._update_status("initialization", "completed", {"components": 6})
            logger.info("Pipeline initialization completed successfully")
            
        except Exception as e:
            self._update_status("initialization", "failed", {}, str(e))
            raise
    
    async def start_pipeline(self):
        """Start the complete pipeline execution"""
        if self.is_running:
            logger.warning("Pipeline is already running")
            return
            
        self.is_running = True
        logger.info("Starting data ingestion pipeline...")
        
        try:
            # Start background tasks
            tasks = [
                asyncio.create_task(self._data_ingestion_loop()),
                asyncio.create_task(self._stream_processing_loop()),
                asyncio.create_task(self._feature_engineering_loop()),
                asyncio.create_task(self._model_inference_loop()),
                asyncio.create_task(self._risk_assessment_loop()),
                asyncio.create_task(self._intervention_loop()),
                asyncio.create_task(self._health_monitoring_loop())
            ]
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            self.is_running = False
            raise
    
    async def stop_pipeline(self):
        """Gracefully stop the pipeline"""
        logger.info("Stopping pipeline...")
        self.is_running = False
        
        # Stop all components
        await self.ingestion_manager.stop()
        await self.stream_processor.stop()
        await self.feature_engine.stop()
        await self.model_manager.stop()
        await self.risk_engine.stop()
        await self.intervention_optimizer.stop()
        
        self._update_status("shutdown", "completed", {})
        logger.info("Pipeline stopped successfully")
    
    async def _data_ingestion_loop(self):
        """Main data ingestion loop"""
        while self.is_running:
            try:
                # Start data collection from multiple sources
                ingestion_metrics = await self.ingestion_manager.collect_data()
                self._update_status("ingestion", "running", ingestion_metrics)
                
                await asyncio.sleep(settings.INGESTION_INTERVAL)
                
            except Exception as e:
                logger.error(f"Data ingestion error: {e}")
                self._update_status("ingestion", "error", {}, str(e))
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _stream_processing_loop(self):
        """Stream processing loop for real-time data"""
        while self.is_running:
            try:
                # Process streaming data from Kafka
                stream_metrics = await self.stream_processor.process_streams()
                self._update_status("streaming", "running", stream_metrics)
                
                await asyncio.sleep(1)  # High frequency processing
                
            except Exception as e:
                logger.error(f"Stream processing error: {e}")
                self._update_status("streaming", "error", {}, str(e))
                await asyncio.sleep(5)
    
    async def _feature_engineering_loop(self):
        """Feature engineering processing loop"""
        while self.is_running:
            try:
                # Extract features from processed data
                feature_metrics = await self.feature_engine.engineer_features()
                self._update_status("feature_engineering", "running", feature_metrics)
                
                await asyncio.sleep(settings.FEATURE_ENGINEERING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Feature engineering error: {e}")
                self._update_status("feature_engineering", "error", {}, str(e))
                await asyncio.sleep(10)
    
    async def _model_inference_loop(self):
        """Model inference processing loop"""
        while self.is_running:
            try:
                # Run ensemble model predictions
                model_metrics = await self.model_manager.run_inference()
                self._update_status("model_inference", "running", model_metrics)
                
                await asyncio.sleep(settings.MODEL_INFERENCE_INTERVAL)
                
            except Exception as e:
                logger.error(f"Model inference error: {e}")
                self._update_status("model_inference", "error", {}, str(e))
                await asyncio.sleep(15)
    
    async def _risk_assessment_loop(self):
        """Risk assessment processing loop"""
        while self.is_running:
            try:
                # Assess risks from model outputs
                risk_metrics = await self.risk_engine.assess_risks()
                self._update_status("risk_assessment", "running", risk_metrics)
                
                await asyncio.sleep(settings.RISK_ASSESSMENT_INTERVAL)
                
            except Exception as e:
                logger.error(f"Risk assessment error: {e}")
                self._update_status("risk_assessment", "error", {}, str(e))
                await asyncio.sleep(10)
    
    async def _intervention_loop(self):
        """Intervention optimization loop"""
        while self.is_running:
            try:
                # Optimize interventions using RL + MAB
                intervention_metrics = await self.intervention_optimizer.optimize()
                self._update_status("intervention", "running", intervention_metrics)
                
                await asyncio.sleep(settings.INTERVENTION_INTERVAL)
                
            except Exception as e:
                logger.error(f"Intervention optimization error: {e}")
                self._update_status("intervention", "error", {}, str(e))
                await asyncio.sleep(20)
    
    async def _health_monitoring_loop(self):
        """Health monitoring and graceful degradation"""
        while self.is_running:
            try:
                # Monitor system health
                health_status = await self._check_system_health()
                
                if health_status["critical_errors"] > 0:
                    logger.warning("Critical errors detected, implementing graceful degradation")
                    await self._implement_graceful_degradation()
                
                await asyncio.sleep(30)  # Health check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        health = {
            "timestamp": datetime.now(),
            "critical_errors": 0,
            "component_status": {},
            "memory_usage": 0,
            "cpu_usage": 0
        }
        
        # Check each component
        components = [
            ("ingestion", self.ingestion_manager),
            ("streaming", self.stream_processor),
            ("features", self.feature_engine),
            ("models", self.model_manager),
            ("risk", self.risk_engine),
            ("intervention", self.intervention_optimizer)
        ]
        
        for name, component in components:
            try:
                status = await component.health_check()
                health["component_status"][name] = status
                if status.get("status") == "critical":
                    health["critical_errors"] += 1
            except Exception as e:
                health["component_status"][name] = {"status": "error", "error": str(e)}
                health["critical_errors"] += 1
        
        return health
    
    async def _implement_graceful_degradation(self):
        """Implement graceful degradation under load"""
        logger.info("Implementing graceful degradation...")
        
        # Reduce processing frequency
        settings.INGESTION_INTERVAL = min(settings.INGESTION_INTERVAL * 2, 300)
        settings.FEATURE_ENGINEERING_INTERVAL = min(settings.FEATURE_ENGINEERING_INTERVAL * 2, 180)
        
        # Switch to simplified models if needed
        await self.model_manager.enable_lightweight_mode()
        
        # Reduce batch sizes
        await self.stream_processor.reduce_batch_size()
        
        self._update_status("degradation", "implemented", {
            "new_intervals": {
                "ingestion": settings.INGESTION_INTERVAL,
                "feature_engineering": settings.FEATURE_ENGINEERING_INTERVAL
            }
        })
    
    def _update_status(self, stage: str, status: str, metrics: Dict[str, Any], error: Optional[str] = None):
        """Update pipeline status"""
        pipeline_status = PipelineStatus(
            stage=stage,
            status=status,
            timestamp=datetime.now(),
            metrics=metrics,
            error=error
        )
        
        self.pipeline_status.append(pipeline_status)
        
        # Keep only last 1000 status updates
        if len(self.pipeline_status) > 1000:
            self.pipeline_status = self.pipeline_status[-1000:]
        
        # Log status update
        if error:
            logger.error(f"Pipeline {stage} failed: {error}")
        else:
            logger.info(f"Pipeline {stage} {status}: {metrics}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        if not self.pipeline_status:
            return {"status": "not_started", "stages": {}}
        
        # Get latest status for each stage
        latest_by_stage = {}
        for status in reversed(self.pipeline_status):
            if status.stage not in latest_by_stage:
                latest_by_stage[status.stage] = asdict(status)
        
        return {
            "is_running": self.is_running,
            "overall_status": "running" if self.is_running else "stopped",
            "stages": latest_by_stage,
            "last_update": self.pipeline_status[-1].timestamp.isoformat()
        }
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline metrics"""
        if not self.pipeline_status:
            return {}
        
        # Calculate metrics from status history
        total_runs = len(self.pipeline_status)
        error_count = sum(1 for s in self.pipeline_status if s.error)
        success_rate = (total_runs - error_count) / total_runs if total_runs > 0 else 0
        
        # Get metrics by stage
        stage_metrics = {}
        for status in self.pipeline_status:
            stage = status.stage
            if stage not in stage_metrics:
                stage_metrics[stage] = {
                    "runs": 0,
                    "errors": 0,
                    "last_metrics": {}
                }
            
            stage_metrics[stage]["runs"] += 1
            if status.error:
                stage_metrics[stage]["errors"] += 1
            stage_metrics[stage]["last_metrics"] = status.metrics
        
        return {
            "total_runs": total_runs,
            "error_count": error_count,
            "success_rate": success_rate,
            "stage_metrics": stage_metrics,
            "uptime_hours": (datetime.now() - self.pipeline_status[0].timestamp).total_seconds() / 3600
        }