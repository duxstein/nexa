#!/usr/bin/env python3
"""
Training script for NEXA AI
This script trains NEXA on various datasets to understand new and complex tasks
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.training.ai_trainer import AITrainer

def setup_logging():
    """Setup logging for training"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('training.log'),
            logging.StreamHandler()
        ]
    )

def train_all_datasets():
    """Train NEXA on all available datasets"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    trainer = AITrainer()
    
    datasets = [
        'application_commands',
        'reminder_commands', 
        'complex_commands'
    ]
    
    results = {}
    
    for dataset_name in datasets:
        logger.info(f"Starting training for dataset: {dataset_name}")
        
        # Train with traditional models
        for model_type in ['naive_bayes', 'svm', 'random_forest']:
            logger.info(f"Training {model_type} model for {dataset_name}")
            result = trainer.train_traditional_model(dataset_name, model_type)
            
            if 'error' not in result:
                results[f"{dataset_name}_{model_type}"] = result
                logger.info(f"✓ {dataset_name}_{model_type}: {result['accuracy']:.2f} accuracy")
            else:
                logger.error(f"✗ {dataset_name}_{model_type}: {result['error']}")
        
        # Train transformer model (optional - takes longer)
        logger.info(f"Training transformer model for {dataset_name}")
        result = trainer.train_transformer_model(dataset_name)
        
        if 'error' not in result:
            results[f"{dataset_name}_transformer"] = result
            logger.info(f"✓ {dataset_name}_transformer: {result['accuracy']:.2f} accuracy")
        else:
            logger.error(f"✗ {dataset_name}_transformer: {result['error']}")
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TRAINING SUMMARY")
    logger.info("="*50)
    
    for model_key, result in results.items():
        if 'error' not in result:
            logger.info(f"{model_key}: {result['accuracy']:.2f} accuracy ({result['dataset_size']} samples)")
    
    logger.info(f"\nTotal trained models: {len(results)}")
    logger.info("Training completed!")
    
    return results

def test_predictions():
    """Test the trained models with sample inputs"""
    trainer = AITrainer()
    
    test_commands = [
        "open chrome browser",
        "remind me to call mom at 3pm",
        "open chrome and search for python tutorials",
        "set reminder for meeting tomorrow",
        "launch spotify and play music"
    ]
    
    models = trainer.get_trained_models()
    
    if not models:
        print("No trained models found. Please run training first.")
        return
    
    print("\nTesting trained models:")
    print("="*50)
    
    for command in test_commands:
        print(f"\nCommand: '{command}'")
        print("-" * 30)
        
        for model_key in models:
            result = trainer.predict_command(command, model_key)
            if 'error' not in result:
                print(f"{model_key}: {result['predicted_command']} (confidence: {result['confidence']:.2f})")
            else:
                print(f"{model_key}: Error - {result['error']}")

def main():
    """Main training function"""
    print("NEXA AI Training System")
    print("=" * 30)
    
    while True:
        print("\nOptions:")
        print("1. Train all datasets")
        print("2. Test predictions")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            results = train_all_datasets()
            print("\nTraining completed! Check training.log for details.")
            
        elif choice == "2":
            test_predictions()
            
        elif choice == "3":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()