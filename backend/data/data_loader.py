import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class KaggleDataLoader:
    """
    Load and process data from Kaggle datasets:
    - IPL: https://www.kaggle.com/datasets/ramjidoolla/ipl-data-set
    - Football: https://www.kaggle.com/datasets/hugomathien/soccer
    - NBA: https://www.kaggle.com/datasets/nathanlauga/nba-games
    - Tennis: https://www.kaggle.com/datasets/hakeem/atp-and-wta-tennis-data
    - Twitter Sentiment: https://www.kaggle.com/datasets/cosmos98/twitter-and-reddit-sentimental-analysis-dataset
    """
    
    def __init__(self, data_path: str = "data/raw"):
        self.data_path = data_path
        self.datasets = {}
        
    def load_ipl_data(self) -> pd.DataFrame:
        """Load IPL cricket data"""
        try:
            # Load matches data
            matches = pd.read_csv(f"{self.data_path}/ipl/matches.csv")
            deliveries = pd.read_csv(f"{self.data_path}/ipl/deliveries.csv")
            
            # Process and aggregate data
            ipl_data = self._process_ipl_data(matches, deliveries)
            
            # Add synthetic sentiment data for demo
            ipl_data['sentiment'] = np.random.uniform(0.3, 0.9, len(ipl_data))
            ipl_data['engagement'] = np.random.uniform(0.4, 0.95, len(ipl_data))
            
            logger.info(f"Loaded {len(ipl_data)} IPL records")
            return ipl_data
            
        except FileNotFoundError:
            logger.warning("IPL dataset not found, generating synthetic data")
            return self._generate_synthetic_cricket_data()
    
    def load_football_data(self) -> pd.DataFrame:
        """Load European football data"""
        try:
            # Load European Soccer Database
            matches = pd.read_csv(f"{self.data_path}/soccer/matches.csv")
            teams = pd.read_csv(f"{self.data_path}/soccer/teams.csv")
            players = pd.read_csv(f"{self.data_path}/soccer/players.csv")
            
            football_data = self._process_football_data(matches, teams, players)
            
            # Add sentiment/engagement
            football_data['sentiment'] = np.random.uniform(0.35, 0.85, len(football_data))
            football_data['engagement'] = np.random.uniform(0.5, 0.9, len(football_data))
            
            logger.info(f"Loaded {len(football_data)} football records")
            return football_data
            
        except FileNotFoundError:
            logger.warning("Football dataset not found, generating synthetic data")
            return self._generate_synthetic_football_data()
    
    def load_nba_data(self) -> pd.DataFrame:
        """Load NBA basketball data"""
        try:
            games = pd.read_csv(f"{self.data_path}/nba/games.csv")
            teams = pd.read_csv(f"{self.data_path}/nba/teams.csv")
            players = pd.read_csv(f"{self.data_path}/nba/players.csv")
            
            nba_data = self._process_nba_data(games, teams, players)
            
            # Add sentiment/engagement
            nba_data['sentiment'] = np.random.uniform(0.4, 0.88, len(nba_data))
            nba_data['engagement'] = np.random.uniform(0.45, 0.92, len(nba_data))
            
            logger.info(f"Loaded {len(nba_data)} NBA records")
            return nba_data
            
        except FileNotFoundError:
            logger.warning("NBA dataset not found, generating synthetic data")
            return self._generate_synthetic_basketball_data()
    
    def load_tennis_data(self) -> pd.DataFrame:
        """Load ATP tennis data"""
        try:
            matches = pd.read_csv(f"{self.data_path}/tennis/atp_matches.csv")
            rankings = pd.read_csv(f"{self.data_path}/tennis/atp_rankings.csv")
            
            tennis_data = self._process_tennis_data(matches, rankings)
            
            # Add sentiment/engagement
            tennis_data['sentiment'] = np.random.uniform(0.38, 0.82, len(tennis_data))
            tennis_data['engagement'] = np.random.uniform(0.4, 0.85, len(tennis_data))
            
            logger.info(f"Loaded {len(tennis_data)} tennis records")
            return tennis_data
            
        except FileNotFoundError:
            logger.warning("Tennis dataset not found, generating synthetic data")
            return self._generate_synthetic_tennis_data()
    
    def load_sentiment_data(self) -> pd.DataFrame:
        """Load Twitter/Reddit sentiment data"""
        try:
            twitter_data = pd.read_csv(f"{self.data_path}/sentiment/twitter_sentiment.csv")
            
            # Process sentiment data
            sentiment_data = self._process_sentiment_data(twitter_data)
            
            logger.info(f"Loaded {len(sentiment_data)} sentiment records")
            return sentiment_data
            
        except FileNotFoundError:
            logger.warning("Sentiment dataset not found, generating synthetic data")
            return self._generate_synthetic_sentiment_data()
    
    def _process_ipl_data(self, matches: pd.DataFrame, deliveries: pd.DataFrame) -> pd.DataFrame:
        """Process IPL cricket data"""
        # Aggregate match statistics
        match_stats = matches.merge(
            deliveries.groupby('match_id').agg({
                'total_runs': 'sum',
                'wicket': 'sum'
            }).reset_index(),
            left_on='id',
            right_on='match_id',
            how='left'
        )
        
        # Extract features
        processed = pd.DataFrame({
            'date': pd.to_datetime(matches['date']),
            'match_type': 'cricket',
            'venue': matches['venue'],
            'team1': matches['team1'],
            'team2': matches['team2'],
            'winner': matches['winner'],
            'win_margin': matches['win_by_runs'].fillna(0) + matches['win_by_wickets'].fillna(0),
            'toss_winner': matches['toss_winner'],
            'toss_decision': matches['toss_decision'],
            'player_of_match': matches['player_of_match'],
            'umpire1': matches['umpire1'],
            'viewership_millions': np.random.uniform(10, 50, len(matches))
        })
        
        return processed
    
    def _process_football_data(self, matches: pd.DataFrame, teams: pd.DataFrame, 
                               players: pd.DataFrame) -> pd.DataFrame:
        """Process football data"""
        # Sample processing
        processed = pd.DataFrame({
            'date': pd.to_datetime(matches.get('date', pd.Series([datetime.now()] * len(matches)))),
            'match_type': 'football',
            'home_team': matches.get('home_team', 'Team A'),
            'away_team': matches.get('away_team', 'Team B'),
            'home_goals': np.random.randint(0, 5, len(matches)),
            'away_goals': np.random.randint(0, 5, len(matches)),
            'possession': np.random.uniform(30, 70, len(matches)),
            'competition': matches.get('league', 'Premier League'),
            'attendance': np.random.randint(10000, 80000, len(matches))
        })
        
        return processed
    
    def _process_nba_data(self, games: pd.DataFrame, teams: pd.DataFrame,
                          players: pd.DataFrame) -> pd.DataFrame:
        """Process NBA data"""
        processed = pd.DataFrame({
            'date': pd.to_datetime(games.get('game_date', pd.Series([datetime.now()] * len(games)))),
            'match_type': 'basketball',
            'home_team': games.get('home_team', 'Lakers'),
            'away_team': games.get('visitor_team', 'Celtics'),
            'home_pts': np.random.randint(80, 130, len(games)),
            'away_pts': np.random.randint(80, 130, len(games)),
            'season': games.get('season', 2023),
            'playoffs': np.random.choice([0, 1], len(games), p=[0.8, 0.2]),
            'attendance': np.random.randint(15000, 20000, len(games))
        })
        
        return processed
    
    def _process_tennis_data(self, matches: pd.DataFrame, rankings: pd.DataFrame) -> pd.DataFrame:
        """Process tennis data"""
        processed = pd.DataFrame({
            'date': pd.to_datetime(matches.get('tourney_date', pd.Series([datetime.now()] * len(matches)))),
            'match_type': 'tennis',
            'tournament': matches.get('tourney_name', 'Wimbledon'),
            'surface': matches.get('surface', 'Hard'),
            'winner': matches.get('winner_name', 'Player A'),
            'loser': matches.get('loser_name', 'Player B'),
            'winner_rank': np.random.randint(1, 100, len(matches)),
            'loser_rank': np.random.randint(1, 100, len(matches)),
            'match_duration': np.random.randint(60, 300, len(matches))
        })
        
        return processed
    
    def _process_sentiment_data(self, twitter_data: pd.DataFrame) -> pd.DataFrame:
        """Process sentiment data"""
        if 'text' in twitter_data.columns and 'sentiment' in twitter_data.columns:
            return twitter_data[['text', 'sentiment', 'created_at']].copy()
        
        # Generate if columns don't exist
        return self._generate_synthetic_sentiment_data()
    
    def _generate_synthetic_cricket_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic cricket data for testing"""
        dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='D')
        
        teams = ['Mumbai Indians', 'Chennai Super Kings', 'Royal Challengers', 
                 'Kolkata Knight Riders', 'Delhi Capitals']
        
        data = pd.DataFrame({
            'date': dates,
            'match_type': 'cricket',
            'team1': np.random.choice(teams, n_samples),
            'team2': np.random.choice(teams, n_samples),
            'venue': np.random.choice(['Wankhede', 'Eden Gardens', 'Chinnaswamy'], n_samples),
            'toss_winner': np.random.choice(teams, n_samples),
            'toss_decision': np.random.choice(['bat', 'field'], n_samples),
            'win_margin': np.random.randint(1, 100, n_samples),
            'viewership_millions': np.random.uniform(10, 50, n_samples),
            'strike_rate': np.random.uniform(100, 200, n_samples),
            'batting_average': np.random.uniform(20, 50, n_samples),
            'is_final': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
            'is_playoff': np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
            'sentiment': np.random.uniform(0.3, 0.9, n_samples),
            'engagement': np.random.uniform(0.4, 0.95, n_samples)
        })
        
        return data
    
    def _generate_synthetic_football_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic football data"""
        dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='D')
        
        teams = ['Manchester United', 'Liverpool', 'Real Madrid', 'Barcelona', 'Bayern Munich']
        competitions = ['Premier League', 'La Liga', 'Champions League', 'Bundesliga']
        
        data = pd.DataFrame({
            'date': dates,
            'match_type': 'football',
            'home_team': np.random.choice(teams, n_samples),
            'away_team': np.random.choice(teams, n_samples),
            'competition': np.random.choice(competitions, n_samples),
            'home_goals': np.random.randint(0, 5, n_samples),
            'away_goals': np.random.randint(0, 5, n_samples),
            'possession': np.random.uniform(30, 70, n_samples),
            'shots_on_target': np.random.randint(1, 15, n_samples),
            'corners': np.random.randint(0, 15, n_samples),
            'fouls': np.random.randint(5, 25, n_samples),
            'attendance': np.random.randint(10000, 80000, n_samples),
            'tv_audience': np.random.uniform(1, 20, n_samples),
            'is_derby': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
            'sentiment': np.random.uniform(0.35, 0.85, n_samples),
            'engagement': np.random.uniform(0.5, 0.9, n_samples)
        })
        
        return data
    
    def _generate_synthetic_basketball_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic NBA data"""
        dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='D')
        
        teams = ['Lakers', 'Celtics', 'Warriors', 'Nets', 'Bulls', 'Heat']
        
        data = pd.DataFrame({
            'date': dates,
            'match_type': 'basketball',
            'home_team': np.random.choice(teams, n_samples),
            'away_team': np.random.choice(teams, n_samples),
            'home_pts': np.random.randint(80, 130, n_samples),
            'away_pts': np.random.randint(80, 130, n_samples),
            'home_rebounds': np.random.randint(30, 60, n_samples),
            'away_rebounds': np.random.randint(30, 60, n_samples),
            'home_assists': np.random.randint(15, 35, n_samples),
            'away_assists': np.random.randint(15, 35, n_samples),
            'season_phase': np.random.choice(['regular', 'playoffs', 'finals'], n_samples, p=[0.8, 0.15, 0.05]),
            'arena_attendance': np.random.randint(15000, 20000, n_samples),
            'national_tv': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
            'player_efficiency': np.random.uniform(10, 30, n_samples),
            'sentiment': np.random.uniform(0.4, 0.88, n_samples),
            'engagement': np.random.uniform(0.45, 0.92, n_samples)
        })
        
        return data
    
    def _generate_synthetic_tennis_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic tennis data"""
        dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='D')
        
        players = ['Djokovic', 'Nadal', 'Federer', 'Alcaraz', 'Medvedev', 'Tsitsipas']
        tournaments = ['Wimbledon', 'US Open', 'French Open', 'Australian Open', 'ATP Finals']
        surfaces = ['Hard', 'Clay', 'Grass']
        rounds = ['R128', 'R64', 'R32', 'R16', 'QF', 'SF', 'F']
        
        data = pd.DataFrame({
            'date': dates,
            'match_type': 'tennis',
            'tournament': np.random.choice(tournaments, n_samples),
            'surface': np.random.choice(surfaces, n_samples),
            'round': np.random.choice(rounds, n_samples),
            'winner': np.random.choice(players, n_samples),
            'loser': np.random.choice(players, n_samples),
            'winner_rank': np.random.randint(1, 100, n_samples),
            'loser_rank': np.random.randint(1, 100, n_samples),
            'winner_aces': np.random.randint(0, 30, n_samples),
            'winner_double_faults': np.random.randint(0, 10, n_samples),
            'match_duration': np.random.randint(60, 300, n_samples),
            'tournament_tier': np.random.randint(1, 5, n_samples),
            'is_final': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
            'top10_matchup': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
            'sentiment': np.random.uniform(0.38, 0.82, n_samples),
            'engagement': np.random.uniform(0.4, 0.85, n_samples)
        })
        
        return data
    
    def _generate_synthetic_sentiment_data(self, n_samples: int = 10000) -> pd.DataFrame:
        """Generate synthetic sentiment data"""
        sports = ['cricket', 'football', 'basketball', 'tennis']
        sentiments = ['positive', 'negative', 'neutral']
        
        sample_texts = {
            'positive': [
                "Amazing match! What a performance!",
                "Best game I've ever seen!",
                "Incredible skills on display today",
                "Team played brilliantly",
                "Outstanding victory!"
            ],
            'negative': [
                "Terrible performance, very disappointed",
                "Worst game ever",
                "Team needs to improve drastically",
                "Completely unacceptable",
                "Very poor showing"
            ],
            'neutral': [
                "Match was okay",
                "Average performance",
                "Nothing special today",
                "Regular game",
                "Standard play"
            ]
        }
        
        texts = []
        labels = []
        sports_list = []
        dates = []
        
        for _ in range(n_samples):
            sentiment = np.random.choice(sentiments)
            text = np.random.choice(sample_texts[sentiment])
            sport = np.random.choice(sports)
            date = datetime.now() - timedelta(days=np.random.randint(0, 365))
            
            texts.append(text)
            labels.append(sentiment)
            sports_list.append(sport)
            dates.append(date)
        
        return pd.DataFrame({
            'text': texts,
            'sentiment': labels,
            'sport': sports_list,
            'created_at': dates
        })
    
    def get_combined_dataset(self) -> pd.DataFrame:
        """Get combined dataset from all sports"""
        cricket_data = self.load_ipl_data()
        football_data = self.load_football_data()
        nba_data = self.load_nba_data()
        tennis_data = self.load_tennis_data()
        
        # Combine all datasets
        combined = pd.concat([
            cricket_data,
            football_data,
            nba_data,
            tennis_data
        ], ignore_index=True)
        
        return combined