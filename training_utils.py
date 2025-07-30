#!/usr/bin/env python3
"""
Training Utilities for NEXA AI
Provides easy-to-use commands for training and managing AI models
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.training.ai_trainer import AITrainer

def create_training_data():
    """Create additional training data examples"""
    trainer = AITrainer()
    
    # Example: Create custom dataset
    custom_data = {
        "description": "Custom commands for specific user needs",
        "task_type": "custom",
        "data": [
            {"text": "open my coding setup", "label": "dev_environment", "confidence": 1.0},
            {"text": "start my work day", "label": "work_routine", "confidence": 1.0},
            {"text": "evening relaxation mode", "label": "relax_mode", "confidence": 1.0}
        ]
    }
    
    trainer.save_dataset("custom_commands", custom_data)
    print("✓ Custom training data created")

def train_specific_dataset(dataset_name, model_type="naive_bayes"):
    """Train a specific dataset with a specific model"""
    trainer = AITrainer()
    
    print(f"Training {dataset_name} with {model_type}...")
    result = trainer.train_traditional_model(dataset_name, model_type)
    
    if 'error' not in result:
        print(f"✓ Training completed!")
        print(f"  Accuracy: {result['accuracy']:.2f}")
        print(f"  Dataset size: {result['dataset_size']}")
    else:
        print(f"✗ Error: {result['error']}")

def list_available_models():
    """List all trained models"""
    trainer = AITrainer()
    models = trainer.get_trained_models()
    
    if not models:
        print("No trained models found.")
        return
    
    print("Available trained models:")
    for model in models:
        print(f"  - {model}")

def test_model_interactive():
    """Interactive model testing"""
    trainer = AITrainer()
    models = trainer.get_trained_models()
    
    if not models:
        print("No trained models available. Please train some models first.")
        return
    
    print("Available models:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")
    
    try:
        model_choice = int(input("\nSelect model (number): ")) - 1
        selected_model = list(models)[model_choice]
    except (ValueError, IndexError):
        print("Invalid selection")
        return
    
    print(f"\nTesting model: {selected_model}")
    print("Enter commands to test (type 'exit' to quit):")
    
    while True:
        command = input("\nCommand: ").strip()
        if command.lower() == 'exit':
            break
        
        if command:
            result = trainer.predict_command(command, selected_model)
            if 'error' not in result:
                print(f"  Prediction: {result['predicted_command']}")
                print(f"  Confidence: {result['confidence']:.2f}")
            else:
                print(f"  Error: {result['error']}")

def export_training_data():
    """Export training data to CSV format"""
    trainer = AITrainer()
    datasets = trainer.get_available_datasets()
    
    for dataset_name in datasets:
        data = trainer.load_dataset(dataset_name)
        if data and 'data' in data:
            csv_filename = f"{dataset_name}.csv"
            
            with open(csv_filename, 'w', encoding='utf-8') as f:
                f.write("text,label,confidence\n")
                for item in data['data']:
                    text = item['text'].replace('"', '""')
                    f.write(f'"{text}",{item["label"]},{item["confidence"]}\n')
            
            print(f"✓ Exported {dataset_name} to {csv_filename}")

def import_training_data(csv_file, dataset_name):
    """Import training data from CSV"""
    try:
        import csv
        
        data = {
            "description": f"Imported from {csv_file}",
            "task_type": "imported",
            "data": []
        }
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data["data"].append({
                    "text": row['text'],
                    "label": row['label'],
                    "confidence": float(row['confidence'])
                })
        
        trainer = AITrainer()
        trainer.save_dataset(dataset_name, data)
        print(f"✓ Imported {len(data['data'])} entries to {dataset_name}")
        
    except Exception as e:
        print(f"✗ Error importing: {e}")

def main():
    """Main utility function"""
    parser = argparse.ArgumentParser(description='NEXA AI Training Utilities')
    parser.add_argument('action', choices=[
        'create-data', 'train', 'list-models', 'test', 'export', 'import'
    ], help='Action to perform')
    parser.add_argument('--dataset', help='Dataset name for training')
    parser.add_argument('--model', default='naive_bayes', help='Model type for training')
    parser.add_argument('--csv', help='CSV file for import/export')
    
    args = parser.parse_args()
    
    if args.action == 'create-data':
        create_training_data()
    elif args.action == 'train':
        if args.dataset:
            train_specific_dataset(args.dataset, args.model)
        else:
            print("Please specify --dataset")
    elif args.action == 'list-models':
        list_available_models()
    elif args.action == 'test':
        test_model_interactive()
    elif args.action == 'export':
        export_training_data()
    elif args.action == 'import':
        if args.csv and args.dataset:
            import_training_data(args.csv, args.dataset)
        else:
            print("Please specify --csv and --dataset")

if __name__ == "__main__":
    main()