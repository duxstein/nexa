# NEXA AI Training System

This document provides comprehensive instructions for training NEXA AI to understand new and complex tasks using datasets and machine learning models.

## Overview

The NEXA AI Training System enables you to train the AI assistant to understand:
- **Application Commands**: Opening, closing, and managing applications
- **Reminder Commands**: Setting, modifying, and managing reminders
- **Complex Commands**: Multi-action commands and custom workflows

## Quick Start

### 1. Initial Setup
```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Train all default datasets
python train_nexa.py --all

# Or train specific datasets
python training_utils.py train --dataset application_commands --model naive_bayes
python training_utils.py train --dataset reminder_commands --model transformer
```

### 2. Testing Your Models
```bash
# Interactive model testing
python training_utils.py test

# List available models
python training_utils.py list-models
```

## Training Data Structure

### Available Datasets

1. **application_commands.json**
   - 100+ variations for opening applications
   - Includes: browsers, office apps, development tools, media apps
   - Examples: "open chrome", "start notepad", "launch visual studio"

2. **reminder_commands.json**
   - 80+ variations for reminder management
   - Includes: time-based, relative, recurring reminders
   - Examples: "remind me in 30 minutes", "set daily reminder at 9am"

3. **complex_commands.json**
   - 50+ complex multi-action commands
   - Includes: workflows, routines, conditional commands
   - Examples: "open chrome and search python", "start work mode"

### Custom Training Data

#### Adding New Commands
1. Create a new JSON file in `training_data/`:
```json
{
  "description": "Your custom commands",
  "task_type": "custom",
  "data": [
    {"text": "your command text", "label": "command_type", "confidence": 1.0}
  ]
}
```

2. Train with your new dataset:
```bash
python training_utils.py train --dataset your_custom_commands --model naive_bayes
```

#### Importing from CSV
```bash
# Create CSV with columns: text,label,confidence
python training_utils.py import --csv your_data.csv --dataset custom_dataset
```

## Model Types

### Traditional ML Models
- **naive_bayes**: Fast, good for text classification
- **svm**: High accuracy, moderate speed
- **random_forest**: Robust, handles noise well

### Transformer Models
- **distilbert-base-uncased**: High accuracy, slower training
- **Custom fine-tuned models**: Best for complex commands

## Configuration

Edit `training_config.json` to customize:
- Model preferences
- Confidence thresholds
- Training intervals
- Logging settings

### Key Configuration Options
```json
{
  "training": {
    "confidence_threshold": 0.7,
    "model_preference": "transformer",
    "fallback_to_rules": true
  }
}
```

## Usage in NEXA

### Basic Usage
The enhanced command processor automatically uses trained models when available:

```python
from src.training.enhanced_command_processor import EnhancedCommandProcessor

processor = EnhancedCommandProcessor()
result = processor.process_command("open chrome and search python")
```

### Advanced Usage
```python
from src.training.ai_trainer import AITrainer

trainer = AITrainer()

# Train custom model
trainer.train_traditional_model("my_commands", "naive_bayes")

# Make predictions
result = trainer.predict_command("my custom command", "my_commands")
```

## Training Workflows

### 1. Batch Training
```bash
# Train all datasets with best models
python train_nexa.py --all --model-type transformer

# Train specific model types
python train_nexa.py --dataset application_commands --model-type svm
```

### 2. Continuous Learning
```bash
# Add new examples and retrain
python training_utils.py import --csv new_examples.csv --dataset application_commands
python training_utils.py train --dataset application_commands --model naive_bayes
```

### 3. Model Evaluation
```bash
# Test model accuracy
python train_nexa.py --test --dataset application_commands

# Interactive testing
python training_utils.py test
```

## Troubleshooting

### Common Issues

1. **"Model not found" error**
   - Ensure you've trained the model first
   - Check `models/` directory for saved models

2. **Low accuracy**
   - Increase training data size
   - Try different model types
   - Adjust confidence threshold

3. **Memory issues with transformer models**
   - Reduce batch size in config
   - Use traditional models for simpler tasks

### Performance Tips

- Use `naive_bayes` for quick prototyping
- Use `transformer` for complex commands
- Cache trained models to avoid retraining
- Monitor training logs in `training.log`

## Examples

### Creating Custom Workflows
```python
# Define custom workflow
workflow_data = {
    "description": "Morning routine",
    "task_type": "workflow",
    "data": [
        {"text": "start my morning", "label": "morning_routine", "confidence": 1.0},
        {"text": "good morning mode", "label": "morning_routine", "confidence": 1.0}
    ]
}

# Train and use
trainer.save_dataset("morning_routine", workflow_data)
trainer.train_traditional_model("morning_routine", "naive_bayes")
```

### Advanced Command Processing
```python
from src.training.enhanced_command_processor import EnhancedCommandProcessor

processor = EnhancedCommandProcessor()

# Process with confidence
try:
    result = processor.process_command("open chrome and search python tutorials")
    if result['confidence'] > 0.8:
        print(f"Executing: {result['action']}")
    else:
        print("Command unclear, using rule-based fallback")
except Exception as e:
    print(f"Error: {e}")
```

## API Reference

### AITrainer Class
- `train_traditional_model(dataset_name, model_type)`
- `train_transformer_model(dataset_name)`
- `predict_command(text, model_name)`
- `save_dataset(name, data)`
- `load_dataset(name)`

### EnhancedCommandProcessor Class
- `process_command(text)` - Main processing method
- `get_trained_models()` - List available models
- `update_confidence_threshold(threshold)`

## Next Steps

1. **Collect User Data**: Gather actual user commands
2. **Refine Models**: Continuously improve based on usage
3. **Add New Domains**: Expand to file management, system control
4. **Implement Active Learning**: Automatically improve from user interactions

## Support

For issues or questions:
1. Check `training.log` for detailed logs
2. Verify dataset format matches examples
3. Ensure all dependencies are installed
4. Test with simple commands first