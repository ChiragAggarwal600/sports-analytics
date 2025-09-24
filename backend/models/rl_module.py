import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
from typing import List, Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PREnvironment:
    """Environment for PR strategy reinforcement learning"""
    
    def __init__(self):
        self.state_dim = 10  # Dimension of state space
        self.action_dim = 5   # Number of possible actions
        self.current_state = None
        self.episode_reward = 0
        self.steps = 0
        
    def reset(self) -> np.ndarray:
        """Reset environment to initial state"""
        self.current_state = np.random.rand(self.state_dim)
        self.episode_reward = 0
        self.steps = 0
        return self.current_state
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute action and return new state, reward, done, info"""
        # Simulate PR action effects
        reward = self._calculate_reward(action)
        
        # Update state based on action
        self.current_state = self._update_state(action)
        
        self.episode_reward += reward
        self.steps += 1
        
        # Episode ends after 24 steps (24 hours)
        done = self.steps >= 24
        
        info = {
            'episode_reward': self.episode_reward,
            'action_taken': action
        }
        
        return self.current_state, reward, done, info
    
    def _calculate_reward(self, action: int) -> float:
        """Calculate reward based on action and current state"""
        # Action 0: No PR activity
        # Action 1: Social media post
        # Action 2: Press release
        # Action 3: Influencer collaboration
        # Action 4: Major campaign
        
        base_rewards = [0, 0.3, 0.5, 0.7, 1.0]
        
        # Adjust reward based on current sentiment and engagement
        sentiment = self.current_state[0]  # Assuming first element is sentiment
        engagement = self.current_state[1]  # Assuming second element is engagement
        
        reward = base_rewards[action]
        
        # Penalize if sentiment is already very positive (oversaturation)
        if sentiment > 0.8 and action > 0:
            reward *= 0.5
            
        # Bonus for good timing
        if engagement > 0.6:
            reward *= 1.5
            
        # Cost of action
        action_costs = [0, 0.1, 0.2, 0.3, 0.5]
        reward -= action_costs[action]
        
        return reward
    
    def _update_state(self, action: int) -> np.ndarray:
        """Update state based on action taken"""
        new_state = self.current_state.copy()
        
        # Simulate state changes
        if action > 0:
            # Increase sentiment (with diminishing returns)
            new_state[0] = min(1.0, new_state[0] + 0.1 * (1 - new_state[0]))
            
            # Temporary boost in engagement
            new_state[1] = min(1.0, new_state[1] + 0.2)
            
        # Natural decay
        new_state[1] *= 0.95  # Engagement decays
        
        # Add some randomness
        new_state += np.random.normal(0, 0.01, self.state_dim)
        new_state = np.clip(new_state, 0, 1)
        
        return new_state

class DQN(nn.Module):
    """Deep Q-Network for PR strategy"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super(DQN, self).__init__()
        
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)
        
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x

class RLPROptimizer:
    """Reinforcement Learning-based PR Strategy Optimizer"""
    
    def __init__(self, state_dim: int = 10, action_dim: int = 5):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Initialize DQN
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.q_network = DQN(state_dim, action_dim).to(self.device)
        self.target_network = DQN(state_dim, action_dim).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=0.001)
        self.memory = deque(maxlen=10000)
        
        # Hyperparameters
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.batch_size = 32
        
        # Environment
        self.env = PREnvironment()
        
    def remember(self, state: np.ndarray, action: int, 
                 reward: float, next_state: np.ndarray, done: bool):
        """Store experience in replay memory"""
        self.memory.append((state, action, reward, next_state, done))
        
    def act(self, state: np.ndarray, training: bool = False) -> int:
        """Choose action using epsilon-greedy policy"""
        if training and random.random() <= self.epsilon:
            return random.randrange(self.action_dim)
            
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        q_values = self.q_network(state_tensor)
        return np.argmax(q_values.cpu().data.numpy())
    
    def replay(self):
        """Train the model on a batch of experiences"""
        if len(self.memory) < self.batch_size:
            return
            
        batch = random.sample(self.memory, self.batch_size)
        states = torch.FloatTensor([e[0] for e in batch]).to(self.device)
        actions = torch.LongTensor([e[1] for e in batch]).to(self.device)
        rewards = torch.FloatTensor([e[2] for e in batch]).to(self.device)
        next_states = torch.FloatTensor([e[3] for e in batch]).to(self.device)
        dones = torch.FloatTensor([e[4] for e in batch]).to(self.device)
        
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        next_q_values = self.target_network(next_states).max(1)[0].detach()
        target_q_values = rewards + (self.gamma * next_q_values * (1 - dones))
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
    def train(self, episodes: int = 100):
        """Train the RL agent"""
        rewards_history = []
        
        for episode in range(episodes):
            state = self.env.reset()
            episode_reward = 0
            
            while True:
                action = self.act(state, training=True)
                next_state, reward, done, _ = self.env.step(action)
                
                self.remember(state, action, reward, next_state, done)
                state = next_state
                episode_reward += reward
                
                if done:
                    break
                    
                self.replay()
                
            rewards_history.append(episode_reward)
            
            # Update target network
            if episode % 10 == 0:
                self.target_network.load_state_dict(self.q_network.state_dict())
                
            if episode % 10 == 0:
                avg_reward = np.mean(rewards_history[-10:])
                logger.info(f"Episode {episode}, Average Reward: {avg_reward:.2f}, Epsilon: {self.epsilon:.3f}")
                
        return rewards_history
    
    def recommend_action(self, current_state: Dict) -> Dict:
        """
        Recommend optimal PR action based on current state
        """
        # Convert dict state to numpy array
        state_vector = self._dict_to_state_vector(current_state)
        
        # Get action from trained network
        action = self.act(state_vector, training=False)
        
        # Map action to strategy
        strategies = [
            {"action": "wait", "description": "No PR activity needed now"},
            {"action": "social_post", "description": "Post on social media"},
            {"action": "press_release", "description": "Issue press release"},
            {"action": "influencer", "description": "Collaborate with influencers"},
            {"action": "campaign", "description": "Launch major PR campaign"}
        ]
        
        recommendation = strategies[action].copy()
        
        # Add confidence and expected impact
        state_tensor = torch.FloatTensor(state_vector).unsqueeze(0).to(self.device)
        q_values = self.q_network(state_tensor).cpu().data.numpy()[0]
        
        recommendation['confidence'] = float(np.max(q_values) - np.mean(q_values))
        recommendation['expected_impact'] = float(np.max(q_values))
        recommendation['alternative_actions'] = [
            strategies[i] for i in np.argsort(q_values)[-3:][::-1] if i != action
        ]
        
        return recommendation
    
    def _dict_to_state_vector(self, state_dict: Dict) -> np.ndarray:
        """Convert dictionary state to numpy vector"""
        vector = np.zeros(self.state_dim)
        
        # Map dict values to vector positions
        vector[0] = state_dict.get('sentiment', 0.5)
        vector[1] = state_dict.get('engagement', 0.5)
        vector[2] = state_dict.get('competitor_activity', 0.5)
        vector[3] = state_dict.get('time_of_day', 12) / 24
        vector[4] = state_dict.get('day_of_week', 3) / 7
        vector[5] = state_dict.get('trending_topics', 0)
        vector[6] = state_dict.get('brand_mentions', 0) / 100
        vector[7] = state_dict.get('crisis_level', 0)
        vector[8] = state_dict.get('opportunity_score', 0.5)
        vector[9] = state_dict.get('budget_remaining', 1.0)
        
        return vector
    
    def save_model(self, path: str):
        """Save trained model"""
        torch.save({
            'q_network': self.q_network.state_dict(),
            'target_network': self.target_network.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, path)
        
    def load_model(self, path: str):
        """Load trained model"""
        checkpoint = torch.load(path, map_location=self.device)
        self.q_network.load_state_dict(checkpoint['q_network'])
        self.target_network.load_state_dict(checkpoint['target_network'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']