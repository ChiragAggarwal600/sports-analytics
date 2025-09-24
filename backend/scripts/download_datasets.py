#!/usr/bin/env python3
"""
Download required datasets from Kaggle
"""

import os
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kaggle dataset URLs
DATASETS = {
    'ipl': 'manasgarg/ipl',
    'football': 'hugomathien/soccer',
    'nba': 'nathanlauga/nba-games',
    'tennis': 'ehallmar/atp-tour-tennis-data',
    'sentiment': 'cosmos98/twitter-and-reddit-sentimental-analysis-dataset'
}

def download_dataset(name: str, dataset_id: str, output_dir: Path):
    """Download a dataset from Kaggle"""
    dataset_dir = output_dir / name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {name} dataset...")
    
    try:
        # Download dataset
        subprocess.run([
            'kaggle', 'datasets', 'download',
            '-d', dataset_id,
            '-p', str(dataset_dir),
            '--unzip'
        ], check=True)
        
        logger.info(f"Successfully downloaded {name} dataset")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to download {name} dataset: {e}")
        return False

def main():
    # Create data directory
    data_dir = Path('data/raw')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Download all datasets
    for name, dataset_id in DATASETS.items():
        download_dataset(name, dataset_id, data_dir)
    
    logger.info("All datasets downloaded successfully!")
    logger.info("You can now run: python scripts/train_models.py")

if __name__ == "__main__":
    # The kaggle library automatically uses KAGGLE_USERNAME and KAGGLE_KEY
    # environment variables for authentication.
    # Make sure they are set before running this script.
    if 'KAGGLE_USERNAME' not in os.environ or 'KAGGLE_KEY' not in os.environ:
        logger.error("Please set KAGGLE_USERNAME and KAGGLE_KEY environment variables.")
        logger.info("You can get your API token from: https://www.kaggle.com/account")
        exit(1)

    try:
        import kaggle
    except ImportError:
        logger.error("The 'kaggle' package is not installed.")
        logger.error("Please install it using your package manager (e.g., 'poetry add kaggle' or 'pip install kaggle').")
        exit(1)
    except OSError as e:
        logger.error(f"An error occurred during Kaggle authentication: {e}")
        logger.error("Please ensure your KAGGLE_USERNAME and KAGGLE_KEY are correct.")
        exit(1)

    main()