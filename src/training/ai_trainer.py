#!/usr/bin/env python3
"""
AI Trainer for NEXA
Handles dataset-based training for new tasks like opening apps, setting reminders, and complex commands
"""

import sys
import os
import json
import logging
import pickle
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from datasets import Dataset

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class AITrainer:
    """Main AI training system for NEXA"""
    
    def __init__(self, training_data_dir: str = "training_data"):
        self.logger = logging.getLogger(__name__)
        self.training_data_dir = Path(training_data_dir)
        self.training_data_dir.mkdir(exist_ok=True)
        
        # Model storage
        self.models_dir = Path("trained_models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Available models
        self.traditional_models = {
            'naive_bayes': MultinomialNB(),
            'svm': SVC(kernel='linear', probability=True),
            'random_forest': RandomForestClassifier(n_estimators=100)
        }
        
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.trained_models = {}
        self.command_mappings = {}
        
        # Load existing models if available
        self._load_trained_models()
    
    def load_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """Load training dataset from JSON file"""
        dataset_path = self.training_data_dir / f"{dataset_name}.json"
        if not dataset_path.exists():
            self.logger.warning(f"Dataset {dataset_name} not found")
            return {}
        
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading dataset {dataset_name}: {e}")
            return {}
    
    def save_dataset(self, dataset_name: str, data: Dict[str, Any]) -> bool:
        """Save training dataset to JSON file"""
        try:
            dataset_path = self.training_data_dir / f"{dataset_name}.json"
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Dataset {dataset_name} saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving dataset {dataset_name}: {e}")
            return False
    
    def train_traditional_model(self, dataset_name: str, model_type: str = 'naive_bayes') -> Dict[str, float]:
        """Train traditional ML model on dataset"""
        dataset = self.load_dataset(dataset_name)
        if not dataset or 'data' not in dataset:
            return {'error': 'Invalid dataset'}
        
        try:
            # Prepare data
            texts = [item['text'] for item in dataset['data']]
            labels = [item['label'] for item in dataset['data']]
            
            # Vectorize text
            X = self.vectorizer.fit_transform(texts)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            model = self.traditional_models[model_type]
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            model_data = {
                'model': model,
                'vectorizer': self.vectorizer,
                'labels': list(set(labels))
            }
            
            model_path = self.models_dir / f"{dataset_name}_{model_type}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            self.trained_models[f"{dataset_name}_{model_type}"] = model_data
            
            return {
                'accuracy': accuracy,
                'model_type': model_type,
                'dataset_size': len(texts),
                'classification_report': classification_report(y_test, y_pred)
            }
            
        except Exception as e:
            self.logger.error(f"Error training traditional model: {e}")
            return {'error': str(e)}
    
    def train_transformer_model(self, dataset_name: str, model_name: str = "distilbert-base-uncased") -> Dict[str, float]:
        """Train transformer-based model using Hugging Face"""
        dataset = self.load_dataset(dataset_name)
        if not dataset or 'data' not in dataset:
            return {'error': 'Invalid dataset'}
        
        try:
            # Prepare data
            texts = [item['text'] for item in dataset['data']]
            labels = [item['label'] for item in dataset['data']]
            label2id = {label: idx for idx, label in enumerate(set(labels))}
            id2label = {idx: label for label, idx in label2id.items()}
            
            # Create Hugging Face dataset
            hf_dataset = Dataset.from_dict({
                'text': texts,
                'label': [label2id[label] for label in labels]
            })
            
            # Split dataset
            dataset_split = hf_dataset.train_test_split(test_size=0.2)
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=len(label2id),
                id2label=id2label,
                label2id=label2id
            )
            
            # Tokenize dataset
            def tokenize_function(examples):
                return tokenizer(examples['text'], padding="max_length", truncation=True)
            
            tokenized_datasets = dataset_split.map(tokenize_function, batched=True)
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=str(self.models_dir / f"{dataset_name}_transformer"),
                evaluation_strategy="epoch",
                per_device_train_batch_size=8,
                per_device_eval_batch_size=8,
                num_train_epochs=3,
                weight_decay=0.01,
            )
            
            # Create trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_datasets['train'],
                eval_dataset=tokenized_datasets['test'],
                compute_metrics=self._compute_metrics,
            )
            
            # Train
            trainer.train()
            
            # Evaluate
            eval_results = trainer.evaluate()
            
            # Save model
            trainer.save_model()
            tokenizer.save_pretrained(str(self.models_dir / f"{dataset_name}_transformer"))
            
            return {
                'accuracy': eval_results['eval_accuracy'],
                'model_type': 'transformer',
                'dataset_size': len(texts),
                'model_path': str(self.models_dir / f"{dataset_name}_transformer")
            }
            
        except Exception as e:
            self.logger.error(f"Error training transformer model: {e}")
            return {'error': str(e)}
    
    def predict_command(self, text: str, model_key: str) -> Dict[str, Any]:
        """Predict command from text using trained model"""
        if model_key not in self.trained_models:
            return {'error': 'Model not found'}
        
        try:
            model_data = self.trained_models[model_key]
            
            if 'transformer' in model_key:
                # Transformer model prediction
                model_path = str(self.models_dir / model_key)
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForSequenceClassification.from_pretrained(model_path)
                
                inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
                with torch.no_grad():
                    outputs = model(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    predicted_class = torch.argmax(predictions, dim=-1).item()
                
                label = model.config.id2label[predicted_class]
                confidence = predictions[0][predicted_class].item()
                
            else:
                # Traditional model prediction
                vectorizer = model_data['vectorizer']
                model = model_data['model']
                
                X = vectorizer.transform([text])
                prediction = model.predict(X)[0]
                confidence = max(model.predict_proba(X)[0]) if hasattr(model, 'predict_proba') else 1.0
                
                label = str(prediction)
            
            return {
                'predicted_command': label,
                'confidence': confidence,
                'text': text
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting command: {e}")
            return {'error': str(e)}
    
    def _load_trained_models(self):
        """Load existing trained models"""
        try:
            for model_file in self.models_dir.glob("*.pkl"):
                model_key = model_file.stem
                with open(model_file, 'rb') as f:
                    self.trained_models[model_key] = pickle.load(f)
                self.logger.info(f"Loaded model: {model_key}")
        except Exception as e:
            self.logger.error(f"Error loading trained models: {e}")
    
    def _compute_metrics(self, eval_pred):
        """Compute metrics for transformer training"""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        return {'accuracy': accuracy_score(labels, predictions)}
    
    def get_available_datasets(self) -> List[str]:
        """Get list of available training datasets"""
        try:
            return [f.stem for f in self.training_data_dir.glob("*.json")]
        except Exception as e:
            self.logger.error(f"Error getting datasets: {e}")
            return []
    
    def get_trained_models(self) -> List[str]:
        """Get list of trained models"""
        return list(self.trained_models.keys())