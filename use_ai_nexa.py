#!/usr/bin/env python3
"""
AI-Enhanced NEXA Launcher
Allows users to easily start NEXA with AI training capabilities
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.nexa_core_enhanced import NexaCoreEnhanced
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from train_nexa import train_all_datasets as train_all_models, test_predictions as test_models

def check_training_data():
    """Check if training data exists"""
    training_data_dir = Path("training_data")
    if not training_data_dir.exists():
        print("❌ Training data directory not found")
        return False
    
    required_files = ["application_commands.json", "reminder_commands.json", "complex_commands.json"]
    missing_files = [f for f in required_files if not (training_data_dir / f).exists()]
    
    if missing_files:
        print(f"❌ Missing training files: {missing_files}")
        return False
    
    return True

def train_models_if_needed():
    """Train models if they don't exist"""
    models_dir = Path("models")
    if not models_dir.exists() or len(list(models_dir.glob("*.pkl"))) == 0:
        print("🔄 No trained models found. Training new models...")
        try:
            train_all_models()
            print("✅ Models trained successfully!")
            return True
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return False
    else:
        print("✅ Trained models found")
        return True

def interactive_demo():
    """Interactive demo of AI capabilities"""
    print("🤖 NEXA AI Training Demo")
    print("=" * 50)
    
    # Check prerequisites
    if not check_training_data():
        print("\nPlease ensure training data files exist in training_data/")
        return
    
    if not train_models_if_needed():
        print("\nTraining failed. Using rule-based fallback.")
    
    # Initialize enhanced NEXA
    print("\n🚀 Starting AI-enhanced NEXA...")
    nexa = NexaCoreEnhanced(use_ai=True)
    
    # Show AI status
    ai_status = nexa.get_ai_status()
    print(f"AI Status: {json.dumps(ai_status, indent=2)}")
    
    print("\n" + "=" * 50)
    print("🎯 AI Command Testing")
    print("Type commands to test AI understanding. Examples:")
    print("  • 'open chrome and search python'")
    print("  • 'remind me to call mom in 30 minutes'")
    print("  • 'start my work setup'")
    print("  • 'close all browsers'")
    print("\nType 'exit' to quit, 'status' for AI info, 'train' to retrain")
    print("=" * 50)
    
    while True:
        try:
            command = input("\n🎤 Command: ").strip()
            
            if command.lower() == 'exit':
                break
            elif command.lower() == 'status':
                status = nexa.get_ai_status()
                print(f"📊 AI Status: {json.dumps(status, indent=2)}")
                continue
            elif command.lower() == 'train':
                print("🔄 Retraining models...")
                result = nexa.train_ai_models()
                print(f"✅ {result}")
                continue
            elif not command:
                continue
            
            # Process command
            print("🔄 Processing...")
            nexa.process_text_command(command)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    nexa.shutdown()

def train_only():
    """Just train models without starting NEXA"""
    print("🎯 Training NEXA AI Models")
    print("=" * 30)
    
    if not check_training_data():
        return
    
    try:
        train_all_models()
        print("✅ All models trained successfully!")
        
        # Test the models
        print("\n🧪 Testing trained models...")
        test_models()
        
    except Exception as e:
        print(f"❌ Training failed: {e}")

def quick_test():
    """Quick test of AI capabilities"""
    print("🧪 Quick AI Test")
    print("=" * 20)
    
    if not train_models_if_needed():
        print("Using rule-based processing...")
        return
    
    try:
        from src.training.ai_trainer import AITrainer
        trainer = AITrainer()
        
        test_commands = [
            "open chrome",
            "remind me to buy groceries",
            "start my coding setup",
            "close all applications"
        ]
        
        for cmd in test_commands:
            result = trainer.predict_command(cmd, "application_commands_naive_bayes")
            if 'error' not in result:
                print(f"✅ '{cmd}' -> {result['predicted_command']} ({result['confidence']:.2f})")
            else:
                print(f"❌ '{cmd}' -> Error: {result['error']}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AI-Enhanced NEXA Launcher")
    parser.add_argument("action", choices=[
        "start", "demo", "train", "test", "status"
    ], help="Action to perform")
    parser.add_argument("--no-ai", action="store_true", help="Use rule-based processing only")
    
    args = parser.parse_args()
    
    if args.action == "start":
        # Start enhanced NEXA
        use_ai = not args.no_ai
        print(f"🚀 Starting NEXA {'with AI' if use_ai else 'without AI'}...")
        
        if use_ai:
            if not train_models_if_needed():
                print("⚠️  Training failed, falling back to rule-based processing")
        
        nexa = NexaCoreEnhanced(use_ai=use_ai)
        print("✅ NEXA is ready! Use Ctrl+C to exit")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            nexa.shutdown()
    
    elif args.action == "demo":
        interactive_demo()
    
    elif args.action == "train":
        train_only()
    
    elif args.action == "test":
        quick_test()
    
    elif args.action == "status":
        print("📊 NEXA AI Status")
        print("=" * 20)
        
        # Check training data
        if check_training_data():
            print("✅ Training data: Available")
        else:
            print("❌ Training data: Missing")
        
        # Check models
        models_dir = Path("models")
        if models_dir.exists():
            model_count = len(list(models_dir.glob("*.pkl")))
            print(f"✅ Trained models: {model_count} available")
        else:
            print("❌ Trained models: None")
        
        # Show config
        try:
            with open('training_config.json', 'r') as f:
                config = json.load(f)
                print(f"✅ AI enabled: {config.get('training', {}).get('enabled', True)}")
        except:
            print("❌ Config: Not found")

if __name__ == "__main__":
    main()