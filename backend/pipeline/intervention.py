"""
Intervention Optimizer
Uses Reinforcement Learning and Multi-Armed Bandits for PR strategy optimization
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
try:
    import aioredis
except ImportError:
    aioredis = None
from collections import defaultdict, deque
import random
from enum import Enum
import statistics

from config.settings import settings

        # settings imported above
logger = logging.getLogger(__name__)

class InterventionType(Enum):
    """Types of interventions available"""
    CRISIS_COMMUNICATION = "crisis_communication"
    PROACTIVE_MESSAGING = "proactive_messaging"
    CONTENT_ADJUSTMENT = "content_adjustment"
    TIMING_OPTIMIZATION = "timing_optimization"
    AUDIENCE_TARGETING = "audience_targeting"
    ENGAGEMENT_BOOST = "engagement_boost"
    SENTIMENT_REPAIR = "sentiment_repair"
    REPUTATION_MANAGEMENT = "reputation_management"

class ActionOutcome(Enum):
    """Possible outcomes of interventions"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    NO_EFFECT = "no_effect"
    NEGATIVE_EFFECT = "negative_effect"

@dataclass
class InterventionAction:
    """Container for intervention actions"""
    id: str
    intervention_type: InterventionType
    description: str
    parameters: Dict[str, Any]
    priority: int
    estimated_impact: float
    confidence: float
    resource_cost: float
    timeline_hours: int
    target_metrics: List[str]
    success_criteria: Dict[str, float]
    created_at: datetime

@dataclass
class InterventionResult:
    """Container for intervention results"""
    action_id: str
    outcome: ActionOutcome
    impact_metrics: Dict[str, float]
    success_score: float
    duration_hours: float
    cost_effectiveness: float
    side_effects: List[str]
    lessons_learned: List[str]
    timestamp: datetime

class MultiArmedBandit:
    """Multi-Armed Bandit for intervention selection"""
    
    def __init__(self, epsilon=0.1, decay_rate=0.995):
        self.epsilon = epsilon  # Exploration rate
        self.decay_rate = decay_rate
        self.arm_counts = defaultdict(int)
        self.arm_rewards = defaultdict(list)
        self.arm_values = defaultdict(float)
        
    def select_arm(self, available_arms: List[str]) -> str:
        """Select arm using epsilon-greedy strategy"""
        if random.random() < self.epsilon:
            # Exploration: random selection
            return random.choice(available_arms)
        else:
            # Exploitation: select best known arm
            best_arm = None
            best_value = float('-inf')
            
            for arm in available_arms:
                if self.arm_values[arm] > best_value:
                    best_value = self.arm_values[arm]
                    best_arm = arm
            
            return best_arm if best_arm else random.choice(available_arms)
    
    def update_arm(self, arm: str, reward: float):
        """Update arm statistics with new reward"""
        self.arm_counts[arm] += 1
        self.arm_rewards[arm].append(reward)
        
        # Update value using moving average
        self.arm_values[arm] = statistics.mean(self.arm_rewards[arm][-100:])  # Last 100 rewards
        
        # Decay exploration rate
        self.epsilon *= self.decay_rate
        self.epsilon = max(self.epsilon, 0.01)  # Minimum exploration rate

class QLearningAgent:
    """Q-Learning agent for intervention optimization"""
    
    def __init__(self, learning_rate=0.1, discount_factor=0.9, epsilon=0.1):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.state_action_counts = defaultdict(lambda: defaultdict(int))
        
    def get_state_key(self, state: Dict[str, Any]) -> str:
        """Convert state to string key for Q-table"""
        # Discretize continuous values
        risk_level = "high" if state.get('risk_score', 0) > 70 else "medium" if state.get('risk_score', 0) > 30 else "low"
        sentiment = "negative" if state.get('sentiment', 0) < -0.1 else "positive" if state.get('sentiment', 0) > 0.1 else "neutral"
        engagement = "high" if state.get('engagement', 0) > 100 else "medium" if state.get('engagement', 0) > 10 else "low"
        
        return f"{risk_level}_{sentiment}_{engagement}"
    
    def select_action(self, state: Dict[str, Any], available_actions: List[str]) -> str:
        """Select action using epsilon-greedy policy"""
        state_key = self.get_state_key(state)
        
        if random.random() < self.epsilon:
            # Exploration
            return random.choice(available_actions)
        else:
            # Exploitation
            best_action = None
            best_value = float('-inf')
            
            for action in available_actions:
                q_value = self.q_table[state_key][action]
                if q_value > best_value:
                    best_value = q_value
                    best_action = action
            
            return best_action if best_action else random.choice(available_actions)
    
    def update_q_value(self, state: Dict[str, Any], action: str, reward: float, next_state: Dict[str, Any]):
        """Update Q-value using Q-learning update rule"""
        state_key = self.get_state_key(state)
        next_state_key = self.get_state_key(next_state)
        
        # Get maximum Q-value for next state
        max_next_q = max(self.q_table[next_state_key].values()) if self.q_table[next_state_key] else 0
        
        # Q-learning update
        current_q = self.q_table[state_key][action]
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        
        self.q_table[state_key][action] = new_q
        self.state_action_counts[state_key][action] += 1
        
        # Decay exploration rate
        self.epsilon *= 0.999
        self.epsilon = max(self.epsilon, 0.01)

class InterventionStrategy:
    """Defines intervention strategies for different scenarios"""
    
    def __init__(self):
        self.strategies = {
            InterventionType.CRISIS_COMMUNICATION: {
                'high_risk_sentiment': [
                    "Issue immediate clarification statement",
                    "Engage with key stakeholders directly",
                    "Provide transparent information",
                    "Acknowledge concerns and outline solutions"
                ],
                'viral_negative_content': [
                    "Rapid response with factual counter-narrative",
                    "Mobilize positive community voices",
                    "Contact platform for content review",
                    "Prepare comprehensive media response"
                ]
            },
            InterventionType.PROACTIVE_MESSAGING: {
                'low_engagement': [
                    "Create compelling visual content",
                    "Share behind-the-scenes content",
                    "Leverage trending topics",
                    "Collaborate with influencers"
                ],
                'neutral_sentiment': [
                    "Share positive achievements",
                    "Highlight community impact",
                    "Post inspirational content",
                    "Engage with fan content"
                ]
            },
            InterventionType.CONTENT_ADJUSTMENT: {
                'poor_performance': [
                    "Analyze top-performing content types",
                    "Adjust posting frequency",
                    "Optimize content timing",
                    "A/B test different formats"
                ]
            },
            InterventionType.REPUTATION_MANAGEMENT: {
                'reputation_risk': [
                    "Monitor competitor activities",
                    "Highlight positive differentiators",
                    "Engage with industry thought leaders",
                    "Publish thought leadership content"
                ]
            }
        }
    
    def get_recommended_actions(self, intervention_type: InterventionType, scenario: str) -> List[str]:
        """Get recommended actions for intervention type and scenario"""
        return self.strategies.get(intervention_type, {}).get(scenario, [])

class InterventionOptimizer:
    """Main intervention optimizer using RL and MAB"""
    
    def __init__(self):
        self.bandit = MultiArmedBandit()
        self.q_agent = QLearningAgent()
        self.strategy = InterventionStrategy()
        self.redis_client = None
        
        # Intervention tracking
        self.active_interventions = {}
        self.intervention_history = deque(maxlen=1000)
        self.performance_metrics = defaultdict(list)
        
        # Available intervention types
        self.available_interventions = list(InterventionType)
        
        # Learning parameters
        self.min_data_points = 10
        self.success_threshold = 0.7
        
    async def initialize(self):
        """Initialize intervention optimizer"""
        try:
            # Initialize Redis client
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Load historical data
            await self._load_intervention_history()
            
            logger.info("Intervention optimizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize intervention optimizer: {e}")
            raise
    
    async def optimize(self) -> Dict[str, Any]:
        """Main optimization loop"""
        optimization_start = datetime.now()
        
        try:
            # Get current system state
            current_state = await self._get_current_state()
            
            # Check if interventions are needed
            intervention_needed = await self._assess_intervention_need(current_state)
            
            if not intervention_needed:
                return {
                    'interventions_generated': 0,
                    'processing_time_seconds': 0,
                    'recommendation': 'No intervention needed',
                    'timestamp': optimization_start.isoformat()
                }
            
            # Generate intervention recommendations
            recommended_actions = await self._generate_interventions(current_state)
            
            # Select optimal intervention using RL/MAB
            selected_action = await self._select_optimal_intervention(current_state, recommended_actions)
            
            # Execute intervention (simulation/logging)
            if selected_action:
                await self._execute_intervention(selected_action)
            
            # Update learning models with recent results
            await self._update_learning_models()
            
            processing_time = (datetime.now() - optimization_start).total_seconds()
            
            return {
                'interventions_generated': len(recommended_actions),
                'selected_intervention': selected_action.intervention_type.value if selected_action else None,
                'processing_time_seconds': processing_time,
                'current_risk_score': current_state.get('risk_score', 0),
                'intervention_confidence': selected_action.confidence if selected_action else 0,
                'timestamp': optimization_start.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Intervention optimization failed: {e}")
            raise
    
    async def _get_current_state(self) -> Dict[str, Any]:
        """Get current system state for decision making"""
        try:
            state = {}
            
            # Get latest risk assessment
            risk_data = await self.redis_client.get('current_risk_assessment')
            if risk_data:
                risk_assessment = json.loads(risk_data)
                state['risk_score'] = risk_assessment.get('overall_risk_score', 0)
                state['risk_level'] = risk_assessment.get('risk_level', 'low')
                state['active_alerts'] = risk_assessment.get('active_alerts_count', 0)
            
            # Get latest sentiment data
            sentiment_entries = await self.redis_client.xread(
                {'stream:predictions': '$'},
                count=10,
                block=500
            )
            
            sentiments = []
            for stream_entries in sentiment_entries:
                for entry_id, entry_data in stream_entries[1]:
                    if 'final_prediction' in entry_data:
                        # Convert prediction to sentiment score
                        pred = float(entry_data['final_prediction'])
                        sentiment = self._prediction_to_sentiment(pred)
                        sentiments.append(sentiment)
            
            if sentiments:
                state['sentiment'] = statistics.mean(sentiments)
            else:
                state['sentiment'] = 0.0
            
            # Get engagement metrics
            engagement_entries = await self.redis_client.xread(
                {'stream:tweets': '$'},
                count=20,
                block=500
            )
            
            engagements = []
            for stream_entries in engagement_entries:
                for entry_id, entry_data in stream_entries[1]:
                    try:
                        engagement = (
                            int(entry_data.get('like_count', 0)) +
                            int(entry_data.get('retweet_count', 0)) +
                            int(entry_data.get('reply_count', 0))
                        )
                        engagements.append(engagement)
                    except (ValueError, TypeError):
                        continue
            
            if engagements:
                state['engagement'] = statistics.mean(engagements)
            else:
                state['engagement'] = 0.0
            
            # Add temporal features
            state['hour_of_day'] = datetime.now().hour
            state['day_of_week'] = datetime.now().weekday()
            state['is_weekend'] = datetime.now().weekday() >= 5
            
            return state
            
        except Exception as e:
            logger.error(f"Error getting current state: {e}")
            return {}
    
    def _prediction_to_sentiment(self, prediction: float) -> float:
        """Convert model prediction to sentiment score"""
        # Assume 0=negative (-0.7), 1=neutral (0.0), 2=positive (0.7)
        if prediction == 0:
            return -0.7
        elif prediction == 1:
            return 0.0
        elif prediction == 2:
            return 0.7
        else:
            return max(-1.0, min(1.0, prediction))
    
    async def _assess_intervention_need(self, state: Dict[str, Any]) -> bool:
        """Assess if intervention is needed based on current state"""
        try:
            # High risk score always needs intervention
            if state.get('risk_score', 0) > 60:
                return True
            
            # Very negative sentiment needs intervention
            if state.get('sentiment', 0) < -0.4:
                return True
            
            # Very low engagement might need intervention
            if state.get('engagement', 0) < 5 and state.get('risk_score', 0) > 30:
                return True
            
            # Multiple alerts indicate need for intervention
            if state.get('active_alerts', 0) > 2:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error assessing intervention need: {e}")
            return False
    
    async def _generate_interventions(self, state: Dict[str, Any]) -> List[InterventionAction]:
        """Generate possible interventions based on current state"""
        try:
            interventions = []
            
            risk_score = state.get('risk_score', 0)
            sentiment = state.get('sentiment', 0)
            engagement = state.get('engagement', 0)
            
            # Crisis communication for high risk
            if risk_score > 70:
                interventions.append(InterventionAction(
                    id=f"crisis_comm_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    intervention_type=InterventionType.CRISIS_COMMUNICATION,
                    description="Immediate crisis communication response",
                    parameters={
                        'urgency': 'high',
                        'channels': ['social_media', 'press_release', 'direct_communication'],
                        'tone': 'transparent_reassuring'
                    },
                    priority=1,
                    estimated_impact=0.8,
                    confidence=0.9,
                    resource_cost=0.8,
                    timeline_hours=2,
                    target_metrics=['risk_score', 'sentiment'],
                    success_criteria={'risk_reduction': 20, 'sentiment_improvement': 0.3},
                    created_at=datetime.now()
                ))
            
            # Sentiment repair for negative sentiment
            if sentiment < -0.3:
                interventions.append(InterventionAction(
                    id=f"sentiment_repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    intervention_type=InterventionType.SENTIMENT_REPAIR,
                    description="Content strategy to repair negative sentiment",
                    parameters={
                        'content_type': 'positive_achievements',
                        'frequency': 'high',
                        'engagement_focus': True
                    },
                    priority=2,
                    estimated_impact=0.6,
                    confidence=0.7,
                    resource_cost=0.5,
                    timeline_hours=12,
                    target_metrics=['sentiment', 'engagement'],
                    success_criteria={'sentiment_improvement': 0.2, 'engagement_increase': 50},
                    created_at=datetime.now()
                ))
            
            # Engagement boost for low engagement
            if engagement < 20:
                interventions.append(InterventionAction(
                    id=f"engagement_boost_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    intervention_type=InterventionType.ENGAGEMENT_BOOST,
                    description="Strategies to increase audience engagement",
                    parameters={
                        'tactics': ['interactive_content', 'trending_topics', 'user_generated_content'],
                        'timing_optimization': True
                    },
                    priority=3,
                    estimated_impact=0.5,
                    confidence=0.6,
                    resource_cost=0.4,
                    timeline_hours=24,
                    target_metrics=['engagement'],
                    success_criteria={'engagement_increase': 100},
                    created_at=datetime.now()
                ))
            
            # Proactive messaging for medium risk
            if 30 <= risk_score <= 60:
                interventions.append(InterventionAction(
                    id=f"proactive_msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    intervention_type=InterventionType.PROACTIVE_MESSAGING,
                    description="Proactive messaging to prevent risk escalation",
                    parameters={
                        'message_type': 'preventive',
                        'stakeholder_focus': True,
                        'transparency_level': 'high'
                    },
                    priority=2,
                    estimated_impact=0.4,
                    confidence=0.8,
                    resource_cost=0.3,
                    timeline_hours=6,
                    target_metrics=['risk_score'],
                    success_criteria={'risk_reduction': 10},
                    created_at=datetime.now()
                ))
            
            # Content adjustment based on performance
            interventions.append(InterventionAction(
                id=f"content_adj_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                intervention_type=InterventionType.CONTENT_ADJUSTMENT,
                description="Adjust content strategy based on current metrics",
                parameters={
                    'optimization_focus': self._determine_optimization_focus(state),
                    'ab_testing': True
                },
                priority=4,
                estimated_impact=0.3,
                confidence=0.5,
                resource_cost=0.2,
                timeline_hours=48,
                target_metrics=['engagement', 'sentiment'],
                success_criteria={'engagement_increase': 25, 'sentiment_improvement': 0.1},
                created_at=datetime.now()
            ))
            
            return interventions
            
        except Exception as e:
            logger.error(f"Error generating interventions: {e}")
            return []
    
    def _determine_optimization_focus(self, state: Dict[str, Any]) -> str:
        """Determine optimization focus based on state"""
        if state.get('engagement', 0) < 10:
            return 'engagement'
        elif state.get('sentiment', 0) < 0:
            return 'sentiment'
        else:
            return 'general'
    
    async def _select_optimal_intervention(self, state: Dict[str, Any], actions: List[InterventionAction]) -> Optional[InterventionAction]:
        """Select optimal intervention using RL and MAB"""
        try:
            if not actions:
                return None
            
            # Use Multi-Armed Bandit for intervention type selection
            intervention_types = [action.intervention_type.value for action in actions]
            selected_type = self.bandit.select_arm(intervention_types)
            
            # Find actions of selected type
            candidate_actions = [action for action in actions if action.intervention_type.value == selected_type]
            
            if not candidate_actions:
                candidate_actions = actions
            
            # Use Q-Learning for specific action selection within type
            if len(candidate_actions) > 1:
                action_ids = [action.id for action in candidate_actions]
                selected_id = self.q_agent.select_action(state, action_ids)
                selected_action = next((action for action in candidate_actions if action.id == selected_id), candidate_actions[0])
            else:
                selected_action = candidate_actions[0]
            
            # Adjust confidence based on learning history
            if selected_type in self.bandit.arm_values:
                historical_performance = self.bandit.arm_values[selected_type]
                selected_action.confidence = min(selected_action.confidence * (1 + historical_performance), 1.0)
            
            return selected_action
            
        except Exception as e:
            logger.error(f"Error selecting optimal intervention: {e}")
            return actions[0] if actions else None
    
    async def _execute_intervention(self, action: InterventionAction):
        """Execute intervention (simulation/logging for now)"""
        try:
            # Add to active interventions
            self.active_interventions[action.id] = {
                'action': action,
                'start_time': datetime.now(),
                'status': 'active'
            }
            
            # Log intervention execution
            execution_data = {
                'action_id': action.id,
                'intervention_type': action.intervention_type.value,
                'description': action.description,
                'parameters': json.dumps(action.parameters),
                'priority': action.priority,
                'estimated_impact': action.estimated_impact,
                'confidence': action.confidence,
                'resource_cost': action.resource_cost,
                'timeline_hours': action.timeline_hours,
                'execution_timestamp': datetime.now().isoformat()
            }
            
            # Store execution record
            await self.redis_client.setex(
                f"intervention_execution:{action.id}",
                timedelta(days=7).total_seconds(),
                json.dumps(execution_data)
            )
            
            # Add to execution stream
            await self.redis_client.xadd(
                'stream:intervention_executions',
                execution_data,
                maxlen=1000
            )
            
            logger.info(f"Executed intervention: {action.intervention_type.value} ({action.id})")
            
            # Simulate intervention outcome (in real implementation, this would be measured)
            await self._simulate_intervention_outcome(action)
            
        except Exception as e:
            logger.error(f"Error executing intervention: {e}")
    
    async def _simulate_intervention_outcome(self, action: InterventionAction):
        """Simulate intervention outcome for learning (placeholder)"""
        try:
            # Simulate some delay
            await asyncio.sleep(1)
            
            # Simulate outcome based on action parameters
            base_success_prob = action.confidence * action.estimated_impact
            
            # Add some randomness
            random_factor = random.uniform(0.5, 1.5)
            success_score = min(base_success_prob * random_factor, 1.0)
            
            # Determine outcome
            if success_score > 0.8:
                outcome = ActionOutcome.SUCCESS
            elif success_score > 0.6:
                outcome = ActionOutcome.PARTIAL_SUCCESS
            elif success_score > 0.3:
                outcome = ActionOutcome.NO_EFFECT
            else:
                outcome = ActionOutcome.NEGATIVE_EFFECT
            
            # Create result
            result = InterventionResult(
                action_id=action.id,
                outcome=outcome,
                impact_metrics={
                    'risk_score_change': random.uniform(-20, 5) if outcome in [ActionOutcome.SUCCESS, ActionOutcome.PARTIAL_SUCCESS] else random.uniform(-5, 10),
                    'sentiment_change': random.uniform(0, 0.3) if outcome in [ActionOutcome.SUCCESS, ActionOutcome.PARTIAL_SUCCESS] else random.uniform(-0.1, 0.1),
                    'engagement_change': random.uniform(0, 100) if outcome in [ActionOutcome.SUCCESS, ActionOutcome.PARTIAL_SUCCESS] else random.uniform(-20, 20)
                },
                success_score=success_score,
                duration_hours=action.timeline_hours + random.uniform(-2, 2),
                cost_effectiveness=success_score / max(action.resource_cost, 0.1),
                side_effects=[],
                lessons_learned=[],
                timestamp=datetime.now()
            )
            
            # Store result and update learning models
            await self._store_intervention_result(result)
            await self._update_learning_with_result(action, result)
            
        except Exception as e:
            logger.error(f"Error simulating intervention outcome: {e}")
    
    async def _store_intervention_result(self, result: InterventionResult):
        """Store intervention result"""
        try:
            result_data = asdict(result)
            result_data['timestamp'] = result.timestamp.isoformat()
            
            # Store result
            await self.redis_client.setex(
                f"intervention_result:{result.action_id}",
                timedelta(days=30).total_seconds(),
                json.dumps(result_data)
            )
            
            # Add to results stream
            await self.redis_client.xadd(
                'stream:intervention_results',
                result_data,
                maxlen=1000
            )
            
            # Add to history
            self.intervention_history.append(result_data)
            
        except Exception as e:
            logger.error(f"Error storing intervention result: {e}")
    
    async def _update_learning_with_result(self, action: InterventionAction, result: InterventionResult):
        """Update learning models with intervention result"""
        try:
            # Update Multi-Armed Bandit
            intervention_type = action.intervention_type.value
            
            # Convert outcome to reward
            reward_mapping = {
                ActionOutcome.SUCCESS: 1.0,
                ActionOutcome.PARTIAL_SUCCESS: 0.6,
                ActionOutcome.NO_EFFECT: 0.3,
                ActionOutcome.NEGATIVE_EFFECT: 0.0
            }
            
            reward = reward_mapping.get(result.outcome, 0.3)
            self.bandit.update_arm(intervention_type, reward)
            
            # Update performance metrics
            self.performance_metrics[intervention_type].append({
                'success_score': result.success_score,
                'cost_effectiveness': result.cost_effectiveness,
                'timestamp': result.timestamp
            })
            
            logger.info(f"Updated learning models: {intervention_type} -> reward: {reward}")
            
        except Exception as e:
            logger.error(f"Error updating learning models: {e}")
    
    async def _update_learning_models(self):
        """Update learning models with recent results"""
        try:
            # Get recent results for Q-Learning updates
            recent_results = await self._get_recent_results()
            
            for result_data in recent_results:
                try:
                    # Reconstruct state transitions for Q-Learning
                    # This is simplified - in real implementation, we'd track state changes
                    action_id = result_data.get('action_id')
                    success_score = result_data.get('success_score', 0)
                    
                    # Use success score as reward for Q-Learning
                    reward = success_score
                    
                    # For now, use dummy states - in real implementation, track actual states
                    dummy_state = {'risk_score': 50, 'sentiment': 0, 'engagement': 50}
                    dummy_next_state = {'risk_score': 45, 'sentiment': 0.1, 'engagement': 60}
                    
                    self.q_agent.update_q_value(dummy_state, action_id, reward, dummy_next_state)
                    
                except Exception as e:
                    logger.error(f"Error updating Q-Learning with result: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error updating learning models: {e}")
    
    async def _get_recent_results(self) -> List[Dict[str, Any]]:
        """Get recent intervention results"""
        try:
            entries = await self.redis_client.xread(
                {'stream:intervention_results': '$'},
                count=50,
                block=1000
            )
            
            results = []
            for stream_entries in entries:
                for entry_id, entry_data in stream_entries[1]:
                    results.append(entry_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting recent results: {e}")
            return []
    
    async def _load_intervention_history(self):
        """Load historical intervention data"""
        try:
            # Load from Redis streams
            history_entries = await self.redis_client.xread(
                {'stream:intervention_results': '0'},
                count=500
            )
            
            for stream_entries in history_entries:
                for entry_id, entry_data in stream_entries[1]:
                    self.intervention_history.append(entry_data)
            
            logger.info(f"Loaded {len(self.intervention_history)} historical intervention records")
            
        except Exception as e:
            logger.error(f"Error loading intervention history: {e}")
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of interventions"""
        try:
            summary = {
                'total_interventions': len(self.intervention_history),
                'intervention_types': {},
                'overall_success_rate': 0.0,
                'avg_cost_effectiveness': 0.0,
                'learning_progress': {}
            }
            
            if not self.intervention_history:
                return summary
            
            # Analyze by intervention type
            type_stats = defaultdict(list)
            
            for result_data in self.intervention_history:
                # This would need to be adjusted based on actual data structure
                intervention_type = result_data.get('intervention_type', 'unknown')
                success_score = float(result_data.get('success_score', 0))
                cost_effectiveness = float(result_data.get('cost_effectiveness', 0))
                
                type_stats[intervention_type].append({
                    'success_score': success_score,
                    'cost_effectiveness': cost_effectiveness
                })
            
            # Calculate statistics
            for intervention_type, stats in type_stats.items():
                success_scores = [s['success_score'] for s in stats]
                cost_scores = [s['cost_effectiveness'] for s in stats]
                
                summary['intervention_types'][intervention_type] = {
                    'count': len(stats),
                    'avg_success_rate': statistics.mean(success_scores),
                    'avg_cost_effectiveness': statistics.mean(cost_scores),
                    'success_std': statistics.stdev(success_scores) if len(success_scores) > 1 else 0
                }
            
            # Overall statistics
            all_success_scores = [float(result.get('success_score', 0)) for result in self.intervention_history]
            all_cost_scores = [float(result.get('cost_effectiveness', 0)) for result in self.intervention_history]
            
            summary['overall_success_rate'] = statistics.mean(all_success_scores) if all_success_scores else 0
            summary['avg_cost_effectiveness'] = statistics.mean(all_cost_scores) if all_cost_scores else 0
            
            # Learning progress
            summary['learning_progress'] = {
                'bandit_arms': len(self.bandit.arm_values),
                'bandit_exploration_rate': self.bandit.epsilon,
                'q_learning_states': len(self.q_table),
                'q_learning_exploration_rate': self.q_agent.epsilon
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for intervention optimizer"""
        try:
            # Check Redis connection
            redis_status = "healthy"
            try:
                await self.redis_client.ping()
            except Exception:
                redis_status = "unhealthy"
            
            # Check learning models
            learning_status = {
                'bandit': 'healthy' if len(self.bandit.arm_values) > 0 else 'no_data',
                'q_learning': 'healthy' if len(self.q_agent.q_table) > 0 else 'no_data'
            }
            
            overall_status = "healthy" if redis_status == "healthy" else "degraded"
            
            return {
                'status': overall_status,
                'components': {
                    'redis': redis_status,
                    'learning_models': learning_status
                },
                'active_interventions': len(self.active_interventions),
                'intervention_history_size': len(self.intervention_history),
                'learning_progress': {
                    'bandit_arms': len(self.bandit.arm_values),
                    'q_states': len(self.q_agent.q_table),
                    'exploration_rates': {
                        'bandit': self.bandit.epsilon,
                        'q_learning': self.q_agent.epsilon
                    }
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def stop(self):
        """Stop intervention optimizer"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Intervention optimizer stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping intervention optimizer: {e}")