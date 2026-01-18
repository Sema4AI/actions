# 🤖 Consolidated Robocorp Task Logs Dashboard with DuckDB WASM

A modern, interactive dashboard that consolidates logs from Producer, Consumer, and Reporter tasks into a single, self-contained HTML file with DuckDB WASM for in-browser analytics.

## 🌟 Features

- **Self-Contained**: Single HTML file with all dependencies embedded
- **Interactive**: Real-time filtering, searching, and data exploration
- **Modern UI**: Responsive design with dark/light theme toggle
- **DuckDB WASM**: In-browser SQL analytics and data processing
- **Comprehensive**: Consolidates logs, work items, screenshots, and errors
- **CI/CD Ready**: Automated generation in GitHub Actions pipeline

## 🏗️ Architecture

```
dashboard/
├── __init__.py                 # Package initialization
├── log_consolidator.py         # DuckDB WASM data ingestion
├── dashboard_generator.py      # HTML dashboard template generator
├── templates/
│   ├── consolidated_dashboard.html  # Main dashboard template
│   └── assets/                     # Static assets (if needed)
└── schema/
    └── logs_schema.sql            # DuckDB table definitions
```

## 📊 Data Schema

The dashboard uses a structured schema to organize task execution data:

- **task_logs**: Individual log entries with timestamps, levels, and messages
- **task_executions**: High-level execution summaries per task
- **work_items**: Work item processing details and status
- **screenshots**: Screenshot metadata and file references
- **performance_metrics**: Task performance data

## 🚀 Usage

### Local Development

Run individual tasks and generate dashboard:

```bash
# Run tasks in sequence
rcc run -t Producer -e devdata/env-for-producer.json
mv output/log.html output/producer-to-consumer/producer-logs.html

rcc run -t Consumer -e devdata/env-for-consumer.json
mv output/log.html output/consumer-to-reporter/consumer-logs.html

rcc run -t Reporter -e devdata/env-for-reporter.json

# Generate consolidated dashboard
python3 scripts/generate_consolidated_dashboard.py
```

### CI/CD Integration

The dashboard is automatically generated in the GitHub Actions workflow:

1. **Producer Task**: Generates work items and logs
2. **Consumer Task**: Processes work items in parallel
3. **Reporter Task**: Aggregates results
4. **Dashboard Generation**: Consolidates all logs and creates dashboard
5. **S3 Upload**: Uploads dashboard to S3 with other artifacts

## 🔧 Configuration

### Environment Variables

- `ROBOT_ARTIFACTS`: Output directory (default: `output`)
- Standard RPA environment variables for task execution

### Dependencies

Added to `conda.yaml`:
- `beautifulsoup4==4.12.2` - HTML parsing
- `lxml==4.9.3` - XML/HTML parser

## 📈 Dashboard Components

### 1. **Overview Statistics**
- Total tasks executed
- Log entries processed
- Success rates
- Screenshot counts

### 2. **Interactive Charts**
- Log level distribution (pie chart)
- Task execution timeline
- Error trends over time

### 3. **Data Explorer Tabs**
- **Task Logs**: Searchable log entries with filtering
- **Work Items**: Processing status and details
- **Screenshots**: Gallery with metadata
- **Error Analysis**: Comprehensive error breakdown

### 4. **Advanced Features**
- **Real-time Search**: Filter across all data types
- **Task Filtering**: Focus on specific tasks (Producer/Consumer/Reporter)
- **Log Level Filtering**: Show only errors, warnings, etc.
- **Theme Toggle**: Dark/light mode support
- **Export Options**: JSON and CSV data exports

## 🎯 Key Benefits

### For Development
- **Debugging**: Comprehensive error analysis and tracing
- **Performance**: Identify bottlenecks and optimization opportunities
- **Monitoring**: Real-time visibility into task execution

### For Operations
- **Reliability**: Track success rates and failure patterns
- **Scalability**: Monitor parallel execution performance
- **Compliance**: Audit trail of all task executions

### For Stakeholders
- **Visibility**: Clear overview of automation health
- **Metrics**: Quantifiable performance indicators
- **Insights**: Data-driven process improvements

## 🔍 Data Processing Flow

1. **Log Collection**: Parses HTML logs from each task
2. **Data Extraction**: Structures timestamps, levels, messages
3. **Work Item Analysis**: Correlates logs with work item processing
4. **Screenshot Indexing**: Catalogs and organizes screenshots
5. **DuckDB Loading**: Imports all data into in-browser database
6. **Dashboard Generation**: Creates interactive HTML with embedded data

## 📱 Mobile-Friendly

The dashboard is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile devices

## 🛡️ Security

- **No External Dependencies**: All JavaScript libraries embedded
- **Client-Side Only**: No server-side processing required
- **Self-Contained**: Single HTML file for easy sharing

## 🚀 Getting Started

1. **Run Your Tasks** following the existing workflow
2. **Generate Dashboard**: Use the provided script or RCC task
3. **Open Dashboard**: Load the HTML file in any modern browser
4. **Explore Data**: Use filters, search, and tabs to analyze results

## 🤝 Integration

The dashboard seamlessly integrates with:
- Existing RPA workflows
- GitHub Actions CI/CD
- S3 artifact storage
- Email notifications (via GitHub Actions)

## 📋 Example Output

After generation, you'll find:
- `consolidated_dashboard.html` - Main dashboard
- `consolidated_data.json` - Raw data export
- `csv_exports/` - Individual CSV files per data type

## 🎨 Customization

The dashboard template can be customized by modifying:
- `templates/consolidated_dashboard.html` - UI layout and styling
- `log_consolidator.py` - Data extraction logic
- `dashboard_generator.py` - Template processing

## 📊 Sample Dashboard Views

### Overview Dashboard
- Executive summary with key metrics
- Visual charts showing trends and distributions
- Quick access to critical information

### Detailed Analysis
- Drill-down into specific tasks or time periods
- Error correlation and root cause analysis
- Performance metrics and optimization insights

### Screenshot Gallery
- Visual debugging with contextual screenshots
- Correlation with specific work items and errors
- Organized by task and timestamp

This dashboard transforms raw RPA logs into actionable insights, enabling better monitoring, debugging, and optimization of your automation processes.