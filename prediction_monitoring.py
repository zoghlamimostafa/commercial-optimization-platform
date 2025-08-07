#!/usr/bin/env python3
"""
Real-time Prediction Monitoring and Alerting System
This module provides continuous monitoring of prediction accuracy
and sends alerts when accuracy drops below acceptable thresholds.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class PredictionMonitor:
    """Real-time prediction accuracy monitoring system"""
    
    def __init__(self, accuracy_threshold=70, alert_enabled=True):
        self.accuracy_threshold = accuracy_threshold  # Minimum acceptable accuracy %
        self.alert_enabled = alert_enabled
        self.monitoring_log = []
        self.alert_history = []
        
    def calculate_prediction_accuracy(self, predictions, actuals):
        """Calculate various accuracy metrics for predictions vs actuals"""
        
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        # Remove any NaN values
        mask = ~(np.isnan(predictions) | np.isnan(actuals))
        predictions = predictions[mask]
        actuals = actuals[mask]
        
        if len(predictions) == 0:
            return {'accuracy': 0, 'error': 'No valid data points'}
            
        # Calculate multiple accuracy metrics
        mae = np.mean(np.abs(predictions - actuals))
        rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((actuals - predictions) / np.maximum(0.1, actuals))) * 100
        
        # Accuracy as percentage (1 - normalized error)
        normalized_error = mae / (np.mean(actuals) + 0.1)
        accuracy = max(0, min(100, 100 * (1 - normalized_error)))
        
        # R-squared
        ss_total = np.sum((actuals - np.mean(actuals)) ** 2)
        ss_residual = np.sum((actuals - predictions) ** 2)
        r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
        
        return {
            'accuracy': accuracy,
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r_squared': r_squared,
            'sample_size': len(predictions),
            'timestamp': datetime.now().isoformat()
        }
    
    def check_prediction_quality(self, predictions):
        """Check prediction quality based on various criteria"""
        
        predictions = np.array(predictions)
        
        quality_issues = []
        
        # Check for unrealistic values
        if np.any(predictions < 0):
            quality_issues.append("Negative predictions detected")
            
        if np.any(predictions > 50):  # Assuming max 50 visits/day is unrealistic
            quality_issues.append("Unusually high predictions detected")
            
        # Check for constant predictions (lack of variance)
        if np.std(predictions) < 0.1:
            quality_issues.append("Very low prediction variance - model may be too conservative")
            
        # Check for excessive variance
        if np.std(predictions) > np.mean(predictions):
            quality_issues.append("High prediction variance - model may be unstable")
            
        # Check for NaN values
        if np.any(np.isnan(predictions)):
            quality_issues.append("NaN values in predictions")
            
        quality_score = max(0, 100 - len(quality_issues) * 20)
        
        return {
            'quality_score': quality_score,
            'issues': quality_issues,
            'predictions_count': len(predictions),
            'mean_prediction': float(np.mean(predictions)),
            'std_prediction': float(np.std(predictions))
        }
    
    def monitor_prediction_accuracy(self, commercial_code, predictions, actuals=None, 
                                   prediction_type='visits'):
        """Monitor prediction accuracy and trigger alerts if needed"""
        
        monitoring_entry = {
            'timestamp': datetime.now().isoformat(),
            'commercial_code': commercial_code,
            'prediction_type': prediction_type,
            'predictions_count': len(predictions)
        }
        
        # Check prediction quality
        quality_check = self.check_prediction_quality(predictions)
        monitoring_entry['quality_check'] = quality_check
        
        # Calculate accuracy if actuals are provided
        if actuals is not None and len(actuals) > 0:
            accuracy_metrics = self.calculate_prediction_accuracy(predictions, actuals)
            monitoring_entry['accuracy_metrics'] = accuracy_metrics
            
            # Check if accuracy is below threshold
            if accuracy_metrics['accuracy'] < self.accuracy_threshold:
                self.trigger_accuracy_alert(commercial_code, accuracy_metrics, prediction_type)
        
        # Check for quality issues
        if quality_check['quality_score'] < 60:  # Quality threshold
            self.trigger_quality_alert(commercial_code, quality_check, prediction_type)
        
        # Log the monitoring entry
        self.monitoring_log.append(monitoring_entry)
        
        # Keep only last 100 entries to avoid memory issues
        if len(self.monitoring_log) > 100:
            self.monitoring_log = self.monitoring_log[-100:]
            
        return monitoring_entry
    
    def trigger_accuracy_alert(self, commercial_code, accuracy_metrics, prediction_type):
        """Trigger an alert when accuracy drops below threshold"""
        
        if not self.alert_enabled:
            return
            
        alert = {
            'type': 'ACCURACY_ALERT',
            'timestamp': datetime.now().isoformat(),
            'commercial_code': commercial_code,
            'prediction_type': prediction_type,
            'accuracy': accuracy_metrics['accuracy'],
            'threshold': self.accuracy_threshold,
            'message': f"Prediction accuracy ({accuracy_metrics['accuracy']:.1f}%) below threshold ({self.accuracy_threshold}%) for commercial {commercial_code}",
            'metrics': accuracy_metrics
        }
        
        self.alert_history.append(alert)
        print(f"🚨 ACCURACY ALERT: {alert['message']}")
        
        # Save alert to file
        self.save_alert_to_file(alert)
    
    def trigger_quality_alert(self, commercial_code, quality_check, prediction_type):
        """Trigger an alert when prediction quality is poor"""
        
        if not self.alert_enabled:
            return
            
        alert = {
            'type': 'QUALITY_ALERT',
            'timestamp': datetime.now().isoformat(),
            'commercial_code': commercial_code,
            'prediction_type': prediction_type,
            'quality_score': quality_check['quality_score'],
            'issues': quality_check['issues'],
            'message': f"Poor prediction quality (score: {quality_check['quality_score']}/100) for commercial {commercial_code}",
            'details': quality_check
        }
        
        self.alert_history.append(alert)
        print(f"⚠️  QUALITY ALERT: {alert['message']}")
        
        # Save alert to file
        self.save_alert_to_file(alert)
    
    def save_alert_to_file(self, alert):
        """Save alert to a log file"""
        try:
            filename = f"prediction_alerts_{datetime.now().strftime('%Y_%m_%d')}.json"
            
            # Try to load existing alerts
            try:
                with open(filename, 'r') as f:
                    alerts = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                alerts = []
            
            # Add new alert
            alerts.append(alert)
            
            # Save back to file
            with open(filename, 'w') as f:
                json.dump(alerts, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save alert to file: {e}")
    
    def generate_monitoring_report(self):
        """Generate a comprehensive monitoring report"""
        
        if not self.monitoring_log:
            return "No monitoring data available"
        
        # Calculate overall statistics
        total_predictions = sum(entry['predictions_count'] for entry in self.monitoring_log)
        
        # Quality scores
        quality_scores = [entry['quality_check']['quality_score'] for entry in self.monitoring_log]
        avg_quality = np.mean(quality_scores)
        
        # Accuracy metrics (if available)
        accuracy_entries = [entry for entry in self.monitoring_log if 'accuracy_metrics' in entry]
        
        report = {
            'summary': {
                'monitoring_period': f"{self.monitoring_log[0]['timestamp']} to {self.monitoring_log[-1]['timestamp']}",
                'total_monitoring_entries': len(self.monitoring_log),
                'total_predictions_monitored': total_predictions,
                'average_quality_score': round(avg_quality, 2),
                'alerts_triggered': len(self.alert_history)
            },
            'quality_analysis': {
                'quality_scores': quality_scores,
                'quality_distribution': {
                    'excellent (90-100)': sum(1 for q in quality_scores if q >= 90),
                    'good (70-89)': sum(1 for q in quality_scores if 70 <= q < 90),
                    'fair (50-69)': sum(1 for q in quality_scores if 50 <= q < 70),
                    'poor (0-49)': sum(1 for q in quality_scores if q < 50)
                }
            },
            'recent_alerts': self.alert_history[-10:] if self.alert_history else []
        }
        
        if accuracy_entries:
            accuracies = [entry['accuracy_metrics']['accuracy'] for entry in accuracy_entries]
            report['accuracy_analysis'] = {
                'entries_with_accuracy': len(accuracy_entries),
                'average_accuracy': round(np.mean(accuracies), 2),
                'accuracy_trend': 'improving' if len(accuracies) > 1 and accuracies[-1] > accuracies[0] else 'stable_or_declining'
            }
        
        return report

def test_monitoring_system():
    """Test the monitoring system with sample data"""
    
    print("=" * 60)
    print("PREDICTION MONITORING SYSTEM TEST")
    print("=" * 60)
    
    # Initialize monitor
    monitor = PredictionMonitor(accuracy_threshold=75, alert_enabled=True)
    
    # Test with sample predictions and actuals
    print("\n1. Testing with good predictions:")
    predictions_good = [5.2, 4.8, 6.1, 5.5, 4.9]
    actuals_good = [5.0, 5.0, 6.0, 5.5, 5.0]
    
    result1 = monitor.monitor_prediction_accuracy('1', predictions_good, actuals_good)
    print(f"   Quality score: {result1['quality_check']['quality_score']}")
    if 'accuracy_metrics' in result1:
        print(f"   Accuracy: {result1['accuracy_metrics']['accuracy']:.1f}%")
    
    # Test with poor predictions
    print("\n2. Testing with poor predictions:")
    predictions_poor = [2.0, 8.0, 1.0, 9.0, 0.5]
    actuals_poor = [5.0, 5.0, 5.0, 5.0, 5.0]
    
    result2 = monitor.monitor_prediction_accuracy('2', predictions_poor, actuals_poor)
    print(f"   Quality score: {result2['quality_check']['quality_score']}")
    if 'accuracy_metrics' in result2:
        print(f"   Accuracy: {result2['accuracy_metrics']['accuracy']:.1f}%")
    
    # Test with unrealistic predictions
    print("\n3. Testing with unrealistic predictions:")
    predictions_unrealistic = [25.0, 30.0, -2.0, 45.0, 100.0]
    
    result3 = monitor.monitor_prediction_accuracy('3', predictions_unrealistic)
    print(f"   Quality score: {result3['quality_check']['quality_score']}")
    print(f"   Issues detected: {result3['quality_check']['issues']}")
    
    # Generate monitoring report
    print("\n4. MONITORING REPORT:")
    print("-" * 25)
    report = monitor.generate_monitoring_report()
    
    print(f"Total monitoring entries: {report['summary']['total_monitoring_entries']}")
    print(f"Average quality score: {report['summary']['average_quality_score']}")
    print(f"Alerts triggered: {report['summary']['alerts_triggered']}")
    
    if 'accuracy_analysis' in report:
        print(f"Average accuracy: {report['accuracy_analysis']['average_accuracy']}%")
    
    print("\nQuality distribution:")
    for category, count in report['quality_analysis']['quality_distribution'].items():
        print(f"  {category}: {count}")
    
    print("\n" + "=" * 60)
    print("MONITORING SYSTEM TEST COMPLETE")
    print("Key features demonstrated:")
    print("- Real-time accuracy monitoring")
    print("- Quality assessment and alerts")
    print("- Comprehensive reporting")
    print("- Alert logging and history")
    print("=" * 60)

if __name__ == "__main__":
    test_monitoring_system()
