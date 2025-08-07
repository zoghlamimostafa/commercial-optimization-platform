"""
Seasonal Pattern Enhancement Module for Commercial Forecasting
Implements advanced seasonality detection and pattern recognition
to improve the accuracy of SARIMA-based forecasting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

class SeasonalPatternEnhancer:
    """Advanced seasonal pattern detection and enhancement system"""
    
    def __init__(self):
        self.weekly_patterns = {}
        self.monthly_patterns = {}
        self.yearly_patterns = {}
        self.holiday_effects = {}
        self.trend_components = {}
        
    def detect_weekly_patterns(self, data, value_column='nombre_visites', date_column='date'):
        """Detect and analyze weekly seasonality patterns"""
        
        patterns = {}
        
        try:
            # Ensure date column is datetime
            data = data.copy()
            data[date_column] = pd.to_datetime(data[date_column])
            
            # Group by commercial and analyze patterns
            for commercial in data['commercial_code'].unique():
                commercial_data = data[data['commercial_code'] == commercial].copy()
                
                if len(commercial_data) < 14:  # Need at least 2 weeks
                    continue
                    
                # Add day of week
                commercial_data['day_of_week'] = commercial_data[date_column].dt.dayofweek
                commercial_data['weekday_name'] = commercial_data[date_column].dt.day_name()
                
                # Calculate weekly patterns
                weekly_stats = commercial_data.groupby('day_of_week')[value_column].agg([
                    'mean', 'std', 'count', 'median'
                ]).round(2)
                
                # Calculate pattern strength (coefficient of variation across days)
                day_means = weekly_stats['mean'].values
                pattern_strength = np.std(day_means) / (np.mean(day_means) + 0.1)
                
                # Detect peak and low days
                peak_day = weekly_stats['mean'].idxmax()
                low_day = weekly_stats['mean'].idxmin()
                
                # Weekend effect analysis
                weekend_avg = weekly_stats.loc[[5, 6], 'mean'].mean()  # Sat, Sun
                weekday_avg = weekly_stats.loc[:4, 'mean'].mean()  # Mon-Fri
                weekend_effect = (weekend_avg - weekday_avg) / (weekday_avg + 0.1)
                
                patterns[commercial] = {
                    'weekly_stats': weekly_stats,
                    'pattern_strength': pattern_strength,
                    'peak_day': peak_day,
                    'low_day': low_day,
                    'weekend_effect': weekend_effect,
                    'weekday_avg': weekday_avg,
                    'weekend_avg': weekend_avg,
                    'has_strong_pattern': pattern_strength > 0.3
                }
                
        except Exception as e:
            print(f"Error in weekly pattern detection: {e}")
            
        self.weekly_patterns = patterns
        return patterns
    
    def detect_monthly_patterns(self, data, value_column='nombre_visites', date_column='date'):
        """Detect monthly and seasonal patterns"""
        
        patterns = {}
        
        try:
            data = data.copy()
            data[date_column] = pd.to_datetime(data[date_column])
            
            for commercial in data['commercial_code'].unique():
                commercial_data = data[data['commercial_code'] == commercial].copy()
                
                if len(commercial_data) < 60:  # Need at least 2 months
                    continue
                
                # Add time components
                commercial_data['month'] = commercial_data[date_column].dt.month
                commercial_data['quarter'] = commercial_data[date_column].dt.quarter
                commercial_data['day_of_month'] = commercial_data[date_column].dt.day
                
                # Monthly patterns
                monthly_stats = commercial_data.groupby('month')[value_column].agg([
                    'mean', 'std', 'count'
                ]).round(2)
                
                # Quarterly patterns
                quarterly_stats = commercial_data.groupby('quarter')[value_column].agg([
                    'mean', 'std', 'count'
                ]).round(2)
                
                # End of month effect
                commercial_data['is_month_end'] = commercial_data['day_of_month'] >= 25
                month_end_effect = commercial_data.groupby('is_month_end')[value_column].mean()
                
                # Seasonal strength
                monthly_means = monthly_stats['mean'].values
                seasonal_strength = np.std(monthly_means) / (np.mean(monthly_means) + 0.1)
                
                patterns[commercial] = {
                    'monthly_stats': monthly_stats,
                    'quarterly_stats': quarterly_stats,
                    'month_end_effect': month_end_effect,
                    'seasonal_strength': seasonal_strength,
                    'peak_month': monthly_stats['mean'].idxmax(),
                    'low_month': monthly_stats['mean'].idxmin(),
                    'has_seasonal_pattern': seasonal_strength > 0.2
                }
                
        except Exception as e:
            print(f"Error in monthly pattern detection: {e}")
            
        self.monthly_patterns = patterns
        return patterns
    
    def detect_holiday_effects(self, data, value_column='nombre_visites', date_column='date'):
        """Detect effects of holidays and special periods"""
        
        effects = {}
        
        try:
            data = data.copy()
            data[date_column] = pd.to_datetime(data[date_column])
            
            # Define French holidays and special periods
            holiday_periods = {
                'new_year': [(1, 1), (1, 2)],  # New Year
                'easter_period': [],  # Will be calculated dynamically
                'labor_day': [(5, 1)],  # May 1st
                'victory_day': [(5, 8)],  # May 8th
                'ascension': [],  # Will be calculated
                'bastille_day': [(7, 14)],  # July 14th
                'assumption': [(8, 15)],  # August 15th
                'all_saints': [(11, 1)],  # November 1st
                'armistice': [(11, 11)],  # November 11th
                'christmas': [(12, 24), (12, 25), (12, 26)],  # Christmas period
                'summer_vacation': [(7, 15), (8, 31)],  # Summer vacation period
                'school_holidays': []  # Will be estimated
            }
            
            for commercial in data['commercial_code'].unique():
                commercial_data = data[data['commercial_code'] == commercial].copy()
                
                if len(commercial_data) < 30:
                    continue
                
                commercial_effects = {}
                
                # Add holiday flags
                commercial_data['month_day'] = commercial_data[date_column].dt.strftime('%m-%d')
                commercial_data['is_holiday'] = False
                
                # Mark known holidays
                for holiday, dates in holiday_periods.items():
                    if dates:  # Skip empty lists
                        holiday_pattern = '|'.join([f"{month:02d}-{day:02d}" for month, day in dates])
                        commercial_data[f'is_{holiday}'] = commercial_data['month_day'].str.match(holiday_pattern)
                        commercial_data['is_holiday'] |= commercial_data[f'is_{holiday}']
                
                # Calculate holiday effects
                if commercial_data['is_holiday'].any():
                    holiday_avg = commercial_data[commercial_data['is_holiday']][value_column].mean()
                    normal_avg = commercial_data[~commercial_data['is_holiday']][value_column].mean()
                    holiday_effect = (holiday_avg - normal_avg) / (normal_avg + 0.1)
                    
                    commercial_effects['general_holiday_effect'] = holiday_effect
                    commercial_effects['holiday_avg'] = holiday_avg
                    commercial_effects['normal_avg'] = normal_avg
                
                # Month-end business effect
                commercial_data['is_month_end'] = commercial_data[date_column].dt.day >= 25
                if commercial_data['is_month_end'].any():
                    month_end_avg = commercial_data[commercial_data['is_month_end']][value_column].mean()
                    month_start_avg = commercial_data[commercial_data[date_column].dt.day <= 10][value_column].mean()
                    month_end_effect = (month_end_avg - month_start_avg) / (month_start_avg + 0.1)
                    
                    commercial_effects['month_end_effect'] = month_end_effect
                
                effects[commercial] = commercial_effects
                
        except Exception as e:
            print(f"Error in holiday effect detection: {e}")
            
        self.holiday_effects = effects
        return effects
    
    def extract_trend_components(self, data, value_column='nombre_visites', date_column='date'):
        """Extract trend components using decomposition"""
        
        components = {}
        
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
            
            data = data.copy()
            data[date_column] = pd.to_datetime(data[date_column])
            
            for commercial in data['commercial_code'].unique():
                commercial_data = data[data['commercial_code'] == commercial].copy()
                
                if len(commercial_data) < 30:
                    continue
                
                # Create time series
                ts = commercial_data.set_index(date_column)[value_column].sort_index()
                
                # Resample to daily frequency and fill gaps
                ts = ts.resample('D').mean().fillna(method='ffill').fillna(method='bfill')
                
                if len(ts) < 14:
                    continue
                
                try:
                    # Perform seasonal decomposition
                    decomposition = seasonal_decompose(
                        ts, 
                        model='additive',
                        period=min(7, len(ts)//2),  # Weekly period or shorter
                        extrapolate_trend='freq'
                    )
                    
                    # Extract components
                    trend = decomposition.trend.dropna()
                    seasonal = decomposition.seasonal.dropna()
                    residual = decomposition.resid.dropna()
                    
                    # Calculate trend strength
                    trend_strength = 1 - np.var(residual) / np.var(trend + residual)
                    seasonal_strength = 1 - np.var(residual) / np.var(seasonal + residual)
                    
                    components[commercial] = {
                        'trend': trend,
                        'seasonal': seasonal,
                        'residual': residual,
                        'trend_strength': max(0, trend_strength),
                        'seasonal_strength': max(0, seasonal_strength),
                        'trend_direction': 'increasing' if trend.iloc[-1] > trend.iloc[0] else 'decreasing',
                        'has_strong_trend': trend_strength > 0.3,
                        'has_strong_seasonality': seasonal_strength > 0.3
                    }
                    
                except Exception as e:
                    print(f"Error in decomposition for commercial {commercial}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in trend component extraction: {e}")
            
        self.trend_components = components
        return components
    
    def generate_enhanced_sarima_params(self, commercial_code, base_params):
        """Generate enhanced SARIMA parameters based on detected patterns"""
        
        enhanced_params = base_params.copy()
        
        try:
            # Get patterns for this commercial
            weekly_pattern = self.weekly_patterns.get(commercial_code, {})
            monthly_pattern = self.monthly_patterns.get(commercial_code, {})
            trend_component = self.trend_components.get(commercial_code, {})
            
            # Adjust seasonal parameters based on detected patterns
            if weekly_pattern.get('has_strong_pattern', False):
                # Strong weekly pattern detected - ensure seasonal component
                enhanced_params['s'] = 7  # Weekly seasonality
                if enhanced_params.get('P', 0) == 0:
                    enhanced_params['P'] = 1  # Add seasonal AR
                if enhanced_params.get('Q', 0) == 0:
                    enhanced_params['Q'] = 1  # Add seasonal MA
                    
            if monthly_pattern.get('has_seasonal_pattern', False):
                # Monthly pattern detected
                if len(self.weekly_patterns.get(commercial_code, {}).get('weekly_stats', {})) >= 30:
                    enhanced_params['s'] = 30  # Monthly seasonality for longer series
                    
            # Adjust differencing based on trend strength
            if trend_component.get('has_strong_trend', False):
                trend_strength = trend_component.get('trend_strength', 0)
                if trend_strength > 0.7:
                    enhanced_params['d'] = min(enhanced_params.get('d', 1) + 1, 2)
                    
            # Adjust seasonal differencing
            seasonal_strength = trend_component.get('seasonal_strength', 0)
            if seasonal_strength > 0.5:
                enhanced_params['D'] = 1
            else:
                enhanced_params['D'] = 0
                
        except Exception as e:
            print(f"Error generating enhanced SARIMA params: {e}")
            
        return enhanced_params
    
    def apply_seasonal_adjustments(self, predictions, commercial_code, prediction_dates):
        """Apply seasonal adjustments to predictions based on detected patterns"""
        
        adjusted_predictions = predictions.copy()
        adjustments_applied = []
        
        try:
            # Get patterns
            weekly_pattern = self.weekly_patterns.get(commercial_code, {})
            monthly_pattern = self.monthly_patterns.get(commercial_code, {})
            holiday_effects = self.holiday_effects.get(commercial_code, {})
            
            # Convert prediction dates to datetime if needed
            if isinstance(prediction_dates, pd.DatetimeIndex):
                dates = prediction_dates
            else:
                dates = pd.to_datetime(prediction_dates)
            
            # Apply weekly adjustments
            if weekly_pattern.get('has_strong_pattern', False):
                weekly_stats = weekly_pattern['weekly_stats']
                overall_mean = weekly_stats['mean'].mean()
                
                for i, date in enumerate(dates):
                    if i < len(adjusted_predictions):
                        day_of_week = date.dayofweek
                        if day_of_week in weekly_stats.index:
                            day_factor = weekly_stats.loc[day_of_week, 'mean'] / overall_mean
                            adjusted_predictions[i] *= day_factor
                            
                adjustments_applied.append('weekly_pattern')
            
            # Apply monthly adjustments
            if monthly_pattern.get('has_seasonal_pattern', False):
                monthly_stats = monthly_pattern['monthly_stats']
                overall_mean = monthly_stats['mean'].mean()
                
                for i, date in enumerate(dates):
                    if i < len(adjusted_predictions):
                        month = date.month
                        if month in monthly_stats.index:
                            month_factor = monthly_stats.loc[month, 'mean'] / overall_mean
                            adjusted_predictions[i] *= month_factor
                            
                adjustments_applied.append('monthly_pattern')
            
            # Apply holiday effects
            if holiday_effects:
                general_effect = holiday_effects.get('general_holiday_effect', 0)
                month_end_effect = holiday_effects.get('month_end_effect', 0)
                
                for i, date in enumerate(dates):
                    if i < len(adjusted_predictions):
                        # Check for holidays (simplified)
                        if date.month == 12 and date.day >= 24:  # Christmas period
                            adjusted_predictions[i] *= (1 + general_effect)
                        elif date.month == 1 and date.day <= 2:  # New Year
                            adjusted_predictions[i] *= (1 + general_effect)
                        elif date.day >= 25:  # Month end
                            adjusted_predictions[i] *= (1 + month_end_effect)
                            
                adjustments_applied.append('holiday_effects')
            
            # Ensure predictions remain within reasonable bounds
            adjusted_predictions = np.clip(adjusted_predictions, 0, 50)
            
        except Exception as e:
            print(f"Error applying seasonal adjustments: {e}")
            adjusted_predictions = predictions
            
        return adjusted_predictions, adjustments_applied
    
    def analyze_all_patterns(self, data):
        """Comprehensive pattern analysis for all commercials"""
        
        print("🔍 SEASONAL PATTERN ANALYSIS")
        print("=" * 50)
        
        # Detect all patterns
        weekly_patterns = self.detect_weekly_patterns(data)
        monthly_patterns = self.detect_monthly_patterns(data)
        holiday_effects = self.detect_holiday_effects(data)
        trend_components = self.extract_trend_components(data)
        
        # Generate summary report
        report = {
            'analysis_date': datetime.now().isoformat(),
            'commercials_analyzed': len(set(data['commercial_code'].unique())),
            'patterns_detected': {
                'strong_weekly_patterns': sum(1 for p in weekly_patterns.values() 
                                            if p.get('has_strong_pattern', False)),
                'seasonal_patterns': sum(1 for p in monthly_patterns.values() 
                                       if p.get('has_seasonal_pattern', False)),
                'trend_patterns': sum(1 for p in trend_components.values() 
                                    if p.get('has_strong_trend', False)),
                'holiday_effects': len(holiday_effects)
            },
            'recommendations': []
        }
        
        # Print detailed analysis
        print(f"📊 Analysis Summary:")
        print(f"   - Commercials analyzed: {report['commercials_analyzed']}")
        print(f"   - Strong weekly patterns: {report['patterns_detected']['strong_weekly_patterns']}")
        print(f"   - Seasonal patterns: {report['patterns_detected']['seasonal_patterns']}")
        print(f"   - Trend patterns: {report['patterns_detected']['trend_patterns']}")
        print(f"   - Holiday effects detected: {report['patterns_detected']['holiday_effects']}")
        
        # Detailed commercial analysis
        print(f"\n📈 Commercial-Specific Patterns:")
        print("-" * 35)
        
        for commercial in data['commercial_code'].unique():
            print(f"\nCommercial {commercial}:")
            
            # Weekly pattern
            if commercial in weekly_patterns:
                wp = weekly_patterns[commercial]
                if wp.get('has_strong_pattern', False):
                    peak_day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][wp['peak_day']]
                    print(f"  ✓ Strong weekly pattern (strength: {wp['pattern_strength']:.2f})")
                    print(f"    Peak day: {peak_day_name}")
                    print(f"    Weekend effect: {wp['weekend_effect']:.2f}")
                else:
                    print(f"  - Weak weekly pattern (strength: {wp.get('pattern_strength', 0):.2f})")
            
            # Monthly pattern
            if commercial in monthly_patterns:
                mp = monthly_patterns[commercial]
                if mp.get('has_seasonal_pattern', False):
                    print(f"  ✓ Seasonal pattern (strength: {mp['seasonal_strength']:.2f})")
                    print(f"    Peak month: {mp['peak_month']}")
                else:
                    print(f"  - Weak seasonal pattern (strength: {mp.get('seasonal_strength', 0):.2f})")
            
            # Trend
            if commercial in trend_components:
                tc = trend_components[commercial]
                if tc.get('has_strong_trend', False):
                    print(f"  ✓ Strong trend ({tc['trend_direction']})")
                    print(f"    Trend strength: {tc['trend_strength']:.2f}")
                    
        # Generate recommendations
        strong_weekly = report['patterns_detected']['strong_weekly_patterns']
        seasonal = report['patterns_detected']['seasonal_patterns']
        
        if strong_weekly > 0:
            report['recommendations'].append(
                f"✓ Use weekly seasonality (s=7) for {strong_weekly} commercials with strong weekly patterns"
            )
        
        if seasonal > 0:
            report['recommendations'].append(
                f"✓ Consider monthly seasonality for {seasonal} commercials with seasonal patterns"
            )
            
        if strong_weekly / report['commercials_analyzed'] > 0.5:
            report['recommendations'].append(
                "✓ Implement day-of-week adjustments for most commercials"
            )
            
        print(f"\n💡 Recommendations:")
        print("-" * 20)
        for rec in report['recommendations']:
            print(f"  {rec}")
            
        return report
    
    def get_enhanced_forecast_params(self, commercial_code):
        """Get optimized forecast parameters for a specific commercial"""
        
        # Default parameters
        params = {
            'p': 1, 'd': 1, 'q': 1,
            'P': 0, 'D': 0, 'Q': 0,
            's': 0
        }
        
        # Get detected patterns
        weekly_pattern = self.weekly_patterns.get(commercial_code, {})
        monthly_pattern = self.monthly_patterns.get(commercial_code, {})
        trend_component = self.trend_components.get(commercial_code, {})
        
        # Adjust based on patterns
        if weekly_pattern.get('has_strong_pattern', False):
            params['s'] = 7
            params['P'] = 1
            params['Q'] = 1
            if weekly_pattern.get('pattern_strength', 0) > 0.5:
                params['D'] = 1
        
        if trend_component.get('has_strong_trend', False):
            if trend_component.get('trend_strength', 0) > 0.7:
                params['d'] = 2
            else:
                params['d'] = 1
                
        return params


def run_seasonal_enhancement_demo():
    """Demonstrate seasonal pattern enhancement capabilities"""
    
    print("🌟 SEASONAL PATTERN ENHANCEMENT DEMO")
    print("=" * 60)
    
    # Create enhanced sample data with realistic patterns
    enhancer = SeasonalPatternEnhancer()
    
    # Generate sample data with clear patterns
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    
    sample_data = []
    for i, date in enumerate(dates):
        # Weekly pattern (higher on weekdays, lower on weekends)
        day_of_week = date.weekday()
        weekly_multiplier = [1.2, 1.3, 1.4, 1.5, 1.3, 0.7, 0.5][day_of_week]
        
        # Monthly pattern (higher in March, September, lower in August, December)
        month = date.month
        monthly_multiplier = {
            1: 0.9, 2: 1.0, 3: 1.4, 4: 1.2, 5: 1.1, 6: 1.0,
            7: 0.9, 8: 0.6, 9: 1.3, 10: 1.1, 11: 1.0, 12: 0.7
        }[month]
        
        # Base visits with some randomness
        base_visits = 5 + np.random.normal(0, 0.5)
        
        # Apply patterns
        visits = base_visits * weekly_multiplier * monthly_multiplier
        visits = max(0, visits)  # No negative visits
        
        sample_data.append({
            'date': date,
            'commercial_code': '1',
            'nombre_visites': visits,
            'client_code': f'CLIENT_{i%10}',
        })
    
    # Add data for another commercial with different patterns
    for i, date in enumerate(dates):
        # Different weekly pattern
        day_of_week = date.weekday()
        weekly_multiplier = [0.8, 1.0, 1.2, 1.4, 1.6, 0.9, 0.6][day_of_week]
        
        # Different monthly pattern
        month = date.month
        monthly_multiplier = {
            1: 1.2, 2: 1.1, 3: 1.0, 4: 0.9, 5: 1.3, 6: 1.4,
            7: 1.5, 8: 1.2, 9: 0.8, 10: 0.9, 11: 1.0, 12: 1.1
        }[month]
        
        base_visits = 4 + np.random.normal(0, 0.3)
        visits = base_visits * weekly_multiplier * monthly_multiplier
        visits = max(0, visits)
        
        sample_data.append({
            'date': date,
            'commercial_code': '2',
            'nombre_visites': visits,
            'client_code': f'CLIENT_{i%8}',
        })
    
    df = pd.DataFrame(sample_data)
    
    print(f"📅 Generated sample data: {len(df)} records")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Commercials: {df['commercial_code'].nunique()}")
    print(f"   Average visits: {df['nombre_visites'].mean():.2f}")
    
    # Run comprehensive analysis
    report = enhancer.analyze_all_patterns(df)
    
    # Test enhanced SARIMA parameters
    print(f"\n🎯 ENHANCED SARIMA PARAMETERS:")
    print("-" * 35)
    
    for commercial in ['1', '2']:
        params = enhancer.get_enhanced_forecast_params(commercial)
        print(f"Commercial {commercial}: {params}")
    
    # Test seasonal adjustments
    print(f"\n🔧 SEASONAL ADJUSTMENT DEMO:")
    print("-" * 30)
    
    future_dates = pd.date_range(start='2025-01-01', periods=14, freq='D')
    base_predictions = np.repeat(5.0, 14)  # Flat prediction
    
    for commercial in ['1', '2']:
        adjusted_preds, adjustments = enhancer.apply_seasonal_adjustments(
            base_predictions, commercial, future_dates
        )
        
        print(f"\nCommercial {commercial}:")
        print(f"  Base prediction: {np.mean(base_predictions):.2f}")
        print(f"  Adjusted prediction: {np.mean(adjusted_preds):.2f}")
        print(f"  Adjustments applied: {', '.join(adjustments)}")
        print(f"  Range: {np.min(adjusted_preds):.1f} - {np.max(adjusted_preds):.1f}")
    
    print(f"\n" + "=" * 60)
    print("SEASONAL PATTERN ENHANCEMENT COMPLETE")
    print("Key capabilities demonstrated:")
    print("- Weekly pattern detection and analysis")
    print("- Monthly/seasonal pattern recognition")
    print("- Holiday and special period effects")
    print("- Trend component extraction")
    print("- Enhanced SARIMA parameter optimization")
    print("- Dynamic seasonal adjustments")
    print("=" * 60)
    
    return enhancer, report


if __name__ == "__main__":
    run_seasonal_enhancement_demo()
