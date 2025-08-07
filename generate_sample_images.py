import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import seaborn as sns

# Create directory if it doesn't exist
os.makedirs('static/visits_images', exist_ok=True)

# Set the aesthetic style of the plots
sns.set_style('whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']

# Generate dates for the x-axis
dates = pd.date_range(start='2023-01-01', periods=52, freq='W')

# 1. Time Series Plot with Trend
plt.figure(figsize=(10, 6))
np.random.seed(42)
trend = np.linspace(50, 100, 52) + np.random.normal(0, 5, 52)
plt.plot(dates, trend, linewidth=2.5, color='#1f77b4')
plt.title('Tendance des Visites Commerciales - 2023', fontsize=14, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Nombre de Visites', fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('static/visits_images/visits_trend.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. SARIMA Forecast
plt.figure(figsize=(10, 6))
# Past data
past_data = trend
# Future dates
future_dates = pd.date_range(start=dates[-1] + pd.Timedelta(days=7), periods=12, freq='W')
all_dates = dates.append(future_dates)
# Forecast with confidence intervals
forecast = past_data[-1] + np.cumsum(np.random.normal(1, 2, 12))
lower_bound = forecast - np.linspace(5, 15, 12)
upper_bound = forecast + np.linspace(5, 15, 12)

plt.plot(dates, past_data, color='#1f77b4', linewidth=2, label='Données historiques')
plt.plot(future_dates, forecast, color='#ff7f0e', linewidth=2.5, label='Prévision SARIMA')
plt.fill_between(future_dates, lower_bound, upper_bound, color='#ff7f0e', alpha=0.2, label='Intervalle de confiance 95%')

plt.axvline(x=dates[-1], color='gray', linestyle='--', alpha=0.7)
plt.title('Prévision SARIMA des Visites Commerciales', fontsize=14, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Nombre de Visites', fontsize=12)
plt.legend(loc='best')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('static/visits_images/visits_forecast.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Commercial Performance Comparison
plt.figure(figsize=(10, 6))
commercial_names = ['Dupont', 'Martin', 'Dubois', 'Bernard', 'Thomas']
visits = np.array([85, 72, 90, 65, 78])
conversions = np.array([42, 35, 48, 30, 37])

x = np.arange(len(commercial_names))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width/2, visits, width, label='Visites', color='#1f77b4')
rects2 = ax.bar(x + width/2, conversions, width, label='Conversions', color='#2ca02c')

ax.set_title('Performance par Commercial - Visites vs Conversions', fontsize=14, fontweight='bold')
ax.set_xlabel('Commercial', fontsize=12)
ax.set_ylabel('Nombre', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(commercial_names)
ax.legend()

# Add labels on top of bars
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

autolabel(rects1)
autolabel(rects2)

plt.tight_layout()
plt.savefig('static/visits_images/commercial_performance.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Visit Efficiency by Region
plt.figure(figsize=(10, 6))
regions = ['Nord', 'Sud', 'Est', 'Ouest', 'Centre']
visits_per_day = np.array([8.2, 6.5, 7.8, 7.1, 6.9])

plt.figure(figsize=(10, 6))
sns.barplot(x=regions, y=visits_per_day, palette='viridis')
plt.title('Efficacité des Visites par Région', fontsize=14, fontweight='bold')
plt.xlabel('Région', fontsize=12)
plt.ylabel('Moyenne de Visites par Jour', fontsize=12)
plt.grid(True, alpha=0.3, axis='y')

for i, v in enumerate(visits_per_day):
    plt.text(i, v + 0.1, f'{v:.1f}', ha='center', fontsize=11)

plt.tight_layout()
plt.savefig('static/visits_images/region_efficiency.png', dpi=300, bbox_inches='tight')
plt.close()

print("Sample images for Commercial Visits Analysis have been generated successfully.")
