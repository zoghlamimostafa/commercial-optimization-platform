# 🚀 Commercial Optimization Platform

> **Commercial & Delivery Optimization System** - An intelligent platform for optimizing commercial performance and logistics with advanced predictive analytics.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.0-purple.svg)](https://getbootstrap.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://mysql.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Overview

This Flask web application provides a comprehensive solution for commercial and logistics optimization, combining:

- **🎯 Advanced Commercial Management** - Performance tracking, client analysis, product management
- **🗺️ Delivery Optimization** - Intelligent route optimization algorithms
- **📈 Predictive Analytics** - SARIMA and Prophet models for accurate forecasting
- **📊 Interactive Dashboards** - Real-time KPIs with modern visualizations
- **💼 Complete Export System** - Excel, CSV, JSON with professional formatting

## ✨ Key Features

### 🏪 **Commercial Management**
- Dashboard with real-time KPIs
- Complete client and sales rep management
- Product performance analysis
- Revenue tracking and trends

### 🚛 **Logistics Optimization**
- Route optimization algorithms (TSP/VRP)
- Intelligent tour planning
- Interactive maps with Leaflet
- Customizable business constraints

### 🔮 **Artificial Intelligence**
- **SARIMA Predictions**: Future commercial visits
- **Prophet Model**: Product sales forecasting
- **Machine Learning**: Classification and optimization
- Confidence intervals and quality metrics

### 📈 **Analytics & Reporting**
- Interactive dashboards
- Charts with Chart.js
- Professional multi-sheet Excel exports
- Keyboard shortcuts for productivity

## 🎬 Quick Preview

### Main Dashboard
![Dashboard](https://via.placeholder.com/800x400/1e40af/ffffff?text=Main+Dashboard+with+Real-time+KPIs)

### Route Optimization
![Routes](https://via.placeholder.com/800x400/059669/ffffff?text=Intelligent+Route+Optimization)

### Predictive Analytics
![Analytics](https://via.placeholder.com/800x400/dc2626/ffffff?text=Advanced+Predictive+Analytics)

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- Node.js (optional, for frontend development)

### Quick Installation

1. **Clone the repository**
```bash
git clone https://github.com/zoghlamimostafa/commercial-optimization-platform.git
cd commercial-optimization-platform
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Database Setup**
```bash
# Create MySQL database 'pfe1'
mysql -u root -p -e "CREATE DATABASE pfe1;"

# Import schema (SQL file not included due to size)
# Contact administrator for database file
```

5. **Run the application**
```bash
python app.py
```

6. **Access the application**
```
http://localhost:5000
```

## 🏗️ Technical Architecture

### Backend
```
app.py (2645+ lines)
├── 🔐 Authentication routes
├── 📊 Data management endpoints
├── 🤖 Predictive analytics API
├── ⚡ Optimization services
├── 📤 Complete export system
└── 🛡️ Error handling and logging
```

### Specialized Modules
- `product_analysis.py` - Product analysis with Prophet
- `commercial_visits_analysis.py` - SARIMA predictions
- `delivery_optimization.py` - Route optimization
- `export_utilities.py` - Centralized export system
- `data_preprocessing.py` - Data cleaning

### Frontend
- **Templates**: Jinja2 with Bootstrap 5
- **Maps**: Leaflet for geolocation
- **Charts**: Chart.js for visualizations
- **UI/UX**: Modern responsive interface
- **Notifications**: SweetAlert2

## 📊 Technology Stack

### Backend Python
```python
Flask                   # Web framework
pandas                  # Data manipulation
numpy                   # Numerical calculations
scikit-learn           # Machine learning
prophet                 # Time series forecasting
statsmodels            # SARIMA models
mysql-connector-python # MySQL connector
openpyxl               # Excel export
matplotlib/seaborn     # Visualizations
```

### Frontend JavaScript
```javascript
Bootstrap 5.3.0        # CSS framework
jQuery 3.6.0           # DOM manipulation
Chart.js               # Interactive charts
Leaflet               # Interactive maps
SweetAlert2           # Elegant notifications
Font Awesome 6        # Modern icons
DataTables            # Advanced tables
```

## 🚀 Usage

### Login
1. Access `http://localhost:5000`
2. Login with your credentials
3. Explore the main dashboard

### Key Features

#### 📊 **Main Dashboard**
- Real-time KPIs (clients, sales reps, products)
- Quick access actions to modules
- Export panel with keyboard shortcuts

#### 👥 **Client Management**
- Complete list with search
- Detailed individual analysis
- Custom Excel/CSV exports

#### 🎯 **Delivery Optimization**
- Sales rep and date selection
- Advanced optimization algorithms
- Interactive map visualization
- Performance metrics

#### 📈 **Predictive Analytics**
- Visit predictions (SARIMA)
- Sales forecasting (Prophet)
- Confidence intervals
- Multi-sales rep comparisons

## 📤 Export System

### Available Export Types
- **📗 Excel**: Multi-sheet with professional formatting
- **📄 CSV**: Lightweight format for external analysis
- **🔗 JSON**: Structured data for API integrations

### Keyboard Shortcuts
- `Ctrl+Shift+C` - Export Clients
- `Ctrl+Shift+V` - Export Sales Reps
- `Ctrl+Shift+P` - Export Products
- `Ctrl+Shift+D` - Export Dashboard
- `Ctrl+Shift+A` - Complete Export

## 🔒 Security

- **Authentication**: Required login with secure sessions
- **Protection**: CSRF, SQL injection, input validation
- **Access Control**: `@login_required` decorator
- **Audit**: Detailed user action logs

## 🎯 Use Cases

### For Sales Representatives
1. View daily performance
2. Plan optimized routes
3. Analyze priority clients
4. Export professional reports

### For Managers
1. Global KPI dashboard
2. Comparative team analysis
3. Business intelligence forecasts
4. Automated reporting

### For Logistics
1. Delivery route optimization
2. Resource planning
3. Efficiency metrics tracking
4. Transport cost analysis

## 📈 Metrics & KPIs

### Commercial Indicators
- Revenue per sales rep/client/product
- Visit frequency and number
- Average basket evolution
- Territorial market share

### Logistics Indicators
- Total optimized distance
- Number of stops per route
- Average delivery time
- Optimization rate (% gain)

### Predictive Indicators
- Forecast accuracy (MAPE)
- Confidence intervals
- Seasonal trends
- Identified sales cycles

## 🤝 Contributing

Contributions are welcome! Here's how to participate:

1. **Fork** the project
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Code Standards
- Follow PEP 8 for Python
- Comment complex code
- Unit tests for new features
- Updated documentation

## 📞 Support

### Documentation
- **📖 Complete Documentation**: `APPLICATION_RESUME_COMPLET.md`
- **🔧 Installation Guide**: Installation section above
- **💡 Usage Examples**: Usage section

### Contact
- **GitHub Issues**: For bugs and feature requests
- **Email**: [contact@example.com](mailto:contact@example.com)
- **Documentation**: Check module README files

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask Team** for the excellent web framework
- **Bootstrap** for the modern user interface
- **Chart.js** for interactive visualizations
- **Leaflet** for geographic maps
- **Prophet & SARIMA** for predictive models

---

## 🌟 Advanced Features

### Artificial Intelligence
- **Time Series Predictions**: SARIMA models for commercial visits
- **Sales Forecasting**: Prophet with seasonality
- **Route Optimization**: Genetic algorithms and heuristics
- **ML Classification**: Automatic client segmentation

### Performance & Scalability
- **Smart Cache**: Optimized query management
- **Asynchronous Processing**: Non-blocking large exports
- **Optimized Indexes**: High-performance database
- **Responsive Design**: Compatible with all devices

### Future Integrations
- **REST API**: Complete endpoints for integrations
- **Webhooks**: Real-time notifications
- **Mobile App**: Native iOS/Android application
- **ERP Integration**: SAP, Oracle connectors, etc.

---

**Developed with ❤️ to optimize commercial and logistics performance**

[![GitHub stars](https://img.shields.io/github/stars/zoghlamimostafa/commercial-optimization-platform.svg?style=social&label=Star)](https://github.com/zoghlamimostafa/commercial-optimization-platform)
[![GitHub forks](https://img.shields.io/github/forks/zoghlamimostafa/commercial-optimization-platform.svg?style=social&label=Fork)](https://github.com/zoghlamimostafa/commercial-optimization-platform/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/zoghlamimostafa/commercial-optimization-platform.svg?style=social&label=Watch)](https://github.com/zoghlamimostafa/commercial-optimization-platform)
