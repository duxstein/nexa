# 🚀 Get Started with NEXA AI Training

Welcome to the AI-enhanced NEXA system! This guide will help you train your AI assistant to understand complex commands and workflows.

## 🎯 Quick Start (2 minutes)

### 1. Train Your First AI Models
```bash
# Train all default datasets
python use_ai_nexa.py train

# Or train specific datasets
python training_utils.py train --dataset application_commands --model naive_bayes
```

### 2. Test Your AI
```bash
# Interactive testing
python use_ai_nexa.py demo

# Quick test
python use_ai_nexa.py test
```

### 3. Start Using AI-Enhanced NEXA
```bash
# Start with AI
python use_ai_nexa.py start

# Start without AI (rule-based)
python use_ai_nexa.py start --no-ai
```

## 📚 Available Commands

### Application Commands (100+ variations)
- "open chrome"
- "start notepad"
- "launch visual studio code"
- "close all browsers"
- "open chrome and search python tutorials"

### Reminder Commands (80+ variations)
- "remind me to call mom in 30 minutes"
- "set daily reminder at 9am"
- "add task to buy groceries tomorrow"
- "remind me every Monday at 8am"

### Complex Commands (50+ variations)
- "start my work setup"
- "evening relaxation mode"
- "open chrome and search stack overflow"
- "close everything and open spotify"

## 🔧 Training Utilities

### Check Status
```bash
python use_ai_nexa.py status
```

### Train Specific Models
```bash
# Naive Bayes (fast, good accuracy)
python training_utils.py train --dataset application_commands --model naive_bayes

# Support Vector Machine (high accuracy)
python training_utils.py train --dataset reminder_commands --model svm

# Transformer (best for complex commands)
python training_utils.py train --dataset complex_commands --model transformer
```

### Interactive Testing
```bash
python training_utils.py test
```

### Export/Import Data
```bash
# Export to CSV
python training_utils.py export

# Import from CSV
python training_utils.py import --csv my_commands.csv --dataset custom_commands
```

## 🎓 Learning Path

### Beginner (Day 1)
1. Run `python use_ai_nexa.py train`
2. Test with `python use_ai_nexa.py demo`
3. Start using `python use_ai_nexa.py start`

### Intermediate (Week 1)
1. Add your own commands to training data
2. Train custom datasets
3. Fine-tune confidence thresholds

### Advanced (Month 1)
1. Create complex workflows
2. Implement active learning
3. Build domain-specific models

## 📝 Adding Your Own Commands

### Method 1: JSON Files
1. Edit `training_data/custom_commands.json`
2. Add your commands:
```json
{
  "description": "My custom commands",
  "task_type": "custom",
  "data": [
    {"text": "my morning routine", "label": "morning_routine", "confidence": 1.0},
    {"text": "start coding session", "label": "dev_mode", "confidence": 1.0}
  ]
}
```
3. Train: `python training_utils.py train --dataset custom_commands`

### Method 2: CSV Import
1. Create `my_commands.csv`:
```csv
text,label,confidence
my morning routine,morning_routine,1.0
start coding session,dev_mode,1.0
```
2. Import: `python training_utils.py import --csv my_commands.csv --dataset my_commands`

## 🔍 Configuration

Edit `training_config.json` to customize:
- Confidence thresholds
- Model preferences
- Training intervals
- Logging levels

## 🐛 Troubleshooting

### Common Issues

**"No trained models found"**
```bash
# Solution: Train models
python use_ai_nexa.py train
```

**"Training failed"**
```bash
# Check training data
python use_ai_nexa.py status

# Install missing dependencies
pip install -r requirements.txt
```

**"Low accuracy"**
```bash
# Try different models
python training_utils.py train --dataset application_commands --model svm

# Add more training data
python training_utils.py import --csv more_data.csv --dataset application_commands
```

### Performance Tips
- Use `naive_bayes` for quick prototyping
- Use `transformer` for complex commands
- Cache trained models to avoid retraining
- Monitor training logs in `training.log`

## 🎮 Examples to Try

### After Training, Try These Commands:

**Application Control:**
```
"open chrome and go to github"
"start visual studio code"
"close all browsers except chrome"
"open spotify and play my playlist"
```

**Reminder Management:**
```
"remind me to check emails in 15 minutes"
"set daily reminder to exercise at 6pm"
"add task to review code tomorrow at 10am"
"remind me every Friday to backup files"
```

**Complex Workflows:**
```
"start my work day"
"evening shutdown routine"
"weekend mode activate"
"focus time - close distractions"
```

## 📊 Monitoring Progress

### Check Model Performance
```bash
python training_utils.py test
```

### View Training Logs
```bash
type training.log
```

### Export Training Data
```bash
python training_utils.py export
```

## 🚀 Next Steps

1. **Collect Real Usage Data**: Start using NEXA and collect actual commands
2. **Refine Models**: Add new variations based on real usage
3. **Expand Domains**: Add file management, system control, etc.
4. **Active Learning**: Implement feedback loops
5. **Custom Workflows**: Build personal automation routines

## 🎉 Success Metrics

You'll know your AI is working well when:
- Commands are understood correctly >90% of the time
- New variations are handled without retraining
- Complex multi-action commands work reliably
- Response time is under 1 second

## 💡 Pro Tips

- Start with simple commands and gradually add complexity
- Use the demo mode to test before full integration
- Keep backup of trained models in `models_backup/`
- Monitor the `training.log` for performance insights
- Join the community to share training datasets and improvements

---

**Ready to start? Run:**
```bash
python use_ai_nexa.py train
```

Happy training! 🤖✨