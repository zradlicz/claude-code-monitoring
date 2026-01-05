# Claude Code Monitoring with Grafana

A complete Docker-based solution for monitoring Claude Code usage with OpenTelemetry, SQLite storage, and Grafana visualization.

## Features

- **Comprehensive Telemetry Collection**: Captures all Claude Code metrics and events via OpenTelemetry
- **User Prompt Tracking**: Records user prompts (when enabled) for complete usage visibility
- **SQLite Storage**: Persistent storage of all telemetry data in an easy-to-query SQLite database
- **Grafana Dashboards**: Pre-configured dashboards for visualizing:
  - Token usage (input/output/cache)
  - Cost tracking
  - Session statistics
  - User prompts
  - Tool usage distribution
  - Lines of code added/removed
  - API requests and errors
- **Docker-based**: Easy deployment with Docker Compose
- **Privacy Controls**: User prompt capture is opt-in with clear warnings

## Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌────────────────┐
│ Claude Code │─gRPC───▶│ OTel Collector   │─HTTP───▶│ SQLite Bridge  │
└─────────────┘         └──────────────────┘         └────────────────┘
                                                              │
                                                              ▼
                                                      ┌────────────────┐
                                                      │ SQLite DB      │
                                                      └────────────────┘
                                                              │
                                                              ▼
                                                      ┌────────────────┐
                                                      │ Grafana        │
                                                      └────────────────┘
```

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Claude Code CLI installed on your machine

## Quick Start

### 1. Set Up the Monitoring Stack

```bash
# Clone or navigate to the project directory
cd claude-code-monitoring

# Run the setup script
chmod +x setup.sh
./setup.sh
```

This will:
- Create necessary directories
- Build the Docker containers
- Start all services (OpenTelemetry Collector, SQLite Bridge, Grafana)

### 2. Configure Claude Code

```bash
# Run the configuration helper
chmod +x configure-claude.sh
./configure-claude.sh
```

This will guide you through setting up the required environment variables.

**Manual Configuration:**

Add these to your `~/.bashrc`, `~/.zshrc`, or shell config:

```bash
# Enable Claude Code telemetry
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# IMPORTANT: Enable user prompt capture (see privacy notes below)
export OTEL_LOG_USER_PROMPTS=1

# Optional: Faster export for testing (default: 60s for metrics, 5s for logs)
# export OTEL_METRIC_EXPORT_INTERVAL=10000
# export OTEL_LOGS_EXPORT_INTERVAL=5000
```

Reload your shell config:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### 3. Access Grafana

1. Open your browser to: http://localhost:3000
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin`
3. You'll be prompted to change the password on first login
4. The "Claude Code Monitoring Dashboard" will be available on the home page

### 4. Use Claude Code

Simply use Claude Code normally:
```bash
claude
```

All metrics and events will be automatically collected and visible in Grafana!

## Dashboard Panels

The pre-configured Grafana dashboard includes:

### Overview Metrics (Top Row)
- **Total Input Tokens (24h)**: Aggregate input token usage
- **Total Output Tokens (24h)**: Aggregate output token usage
- **Total Cost (24h)**: Total cost in USD
- **Sessions Started (24h)**: Number of Claude Code sessions

### Time Series Graphs
- **Token Usage Over Time**: Input and output tokens trending
- **Cost Over Time**: USD cost trending
- **Lines of Code Added/Removed**: Code modification activity

### Tables
- **Recent User Prompts**: List of recent prompts with preview (when enabled)
- **Recent API Requests**: Detailed API call information
- **API Errors**: Error tracking and debugging

### Distribution Charts
- **Tool Usage Distribution**: Pie chart of tool usage (Read, Write, Edit, Bash, etc.)

## Privacy & Security

### ⚠️ Important: User Prompt Capture

By default, Claude Code **does not** capture the content of user prompts - only the prompt length is recorded.

To capture full prompt content, you must explicitly set:
```bash
export OTEL_LOG_USER_PROMPTS=1
```

**Privacy Considerations:**
- Full prompts may contain sensitive information (code, credentials, private data)
- Only enable this if you control the monitoring infrastructure
- Ensure you have proper data handling and retention policies
- The SQLite database file will contain all captured data

**Without OTEL_LOG_USER_PROMPTS=1:**
- Only prompt length is recorded
- No prompt content is stored
- Still provides valuable usage metrics

### Data Storage

- All data is stored in `./data/claude_monitoring.db`
- This is a SQLite database file mounted from your host
- You can back up, query, or delete this file as needed
- No data is sent to external services

## Service Endpoints

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Grafana | http://localhost:3000 | Visualization dashboard |
| SQLite Bridge Stats | http://localhost:5000/stats | Database statistics API |
| SQLite Bridge Health | http://localhost:5000/health | Health check |
| OTel Collector (gRPC) | grpc://localhost:4317 | Claude Code telemetry endpoint |
| OTel Collector (HTTP) | http://localhost:4318 | Alternative telemetry endpoint |

## Management Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f sqlite-bridge
docker-compose logs -f otel-collector
docker-compose logs -f grafana
```

### Check Service Status
```bash
docker-compose ps
```

### Restart Services
```bash
docker-compose restart
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove All Data
```bash
docker-compose down -v
rm -rf data/
```

### Query SQLite Database Directly
```bash
# Install sqlite3 if needed
# Access the database
sqlite3 data/claude_monitoring.db

# Example queries
.tables
SELECT COUNT(*) FROM metrics;
SELECT COUNT(*) FROM events;
SELECT * FROM events WHERE event_name = 'claude_code.user_prompt' LIMIT 5;
```

## Troubleshooting

### Claude Code not sending telemetry

1. Verify environment variables are set:
   ```bash
   echo $CLAUDE_CODE_ENABLE_TELEMETRY
   echo $OTEL_EXPORTER_OTLP_ENDPOINT
   ```

2. Check if services are running:
   ```bash
   docker-compose ps
   ```

3. Check OTel collector logs:
   ```bash
   docker-compose logs otel-collector
   ```

4. Verify connectivity:
   ```bash
   curl http://localhost:5000/health
   curl http://localhost:5000/stats
   ```

### No data in Grafana

1. Check if SQLite database has data:
   ```bash
   sqlite3 data/claude_monitoring.db "SELECT COUNT(*) FROM metrics;"
   ```

2. Verify Grafana datasource:
   - Go to Configuration → Data Sources
   - Check "Claude Code Monitoring" datasource
   - Click "Test" button

3. Check SQLite bridge logs:
   ```bash
   docker-compose logs sqlite-bridge
   ```

### Permission issues with data directory

```bash
# Fix permissions
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

## Advanced Configuration

### Custom Resource Attributes

Add custom attributes to all metrics for multi-team tracking:

```bash
export OTEL_RESOURCE_ATTRIBUTES="department=engineering,team=platform,cost_center=eng-123"
```

These will appear in the `custom_attributes` JSON field in the database.

### Remote Monitoring Server

To monitor Claude Code from a different machine:

1. On the monitoring server, ensure port 4317 is accessible
2. Update firewall rules if needed
3. On the Claude Code machine:
   ```bash
   export OTEL_EXPORTER_OTLP_ENDPOINT=http://your-server-ip:4317
   ```

### Retention and Cleanup

The database will grow over time. To manage size:

```bash
# Delete old data (older than 30 days)
sqlite3 data/claude_monitoring.db "DELETE FROM metrics WHERE timestamp < datetime('now', '-30 days');"
sqlite3 data/claude_monitoring.db "DELETE FROM events WHERE timestamp < datetime('now', '-30 days');"

# Vacuum to reclaim space
sqlite3 data/claude_monitoring.db "VACUUM;"
```

Consider setting up a cron job for automatic cleanup.

## Database Schema

### Metrics Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | DATETIME | Metric timestamp |
| session_id | TEXT | Claude Code session identifier |
| account_uuid | TEXT | User account UUID |
| organization_id | TEXT | Organization UUID |
| terminal_type | TEXT | Terminal type (iTerm, VSCode, etc.) |
| app_version | TEXT | Claude Code version |
| metric_name | TEXT | Metric name (e.g., claude_code.token.usage) |
| metric_value | REAL | Metric value |
| metric_unit | TEXT | Unit of measurement |
| model | TEXT | Claude model used |
| type | TEXT | Metric type (input, output, added, removed, etc.) |
| tool | TEXT | Tool name for tool-specific metrics |
| decision | TEXT | Decision (accept/reject) |
| language | TEXT | Programming language |
| custom_attributes | TEXT | Additional attributes as JSON |

### Events Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | DATETIME | Event timestamp |
| session_id | TEXT | Claude Code session identifier |
| account_uuid | TEXT | User account UUID |
| organization_id | TEXT | Organization UUID |
| terminal_type | TEXT | Terminal type |
| app_version | TEXT | Claude Code version |
| event_name | TEXT | Event name (e.g., claude_code.user_prompt) |
| prompt | TEXT | User prompt content (if enabled) |
| prompt_length | INTEGER | Length of prompt |
| tool_name | TEXT | Tool name |
| success | TEXT | Success status |
| duration_ms | INTEGER | Duration in milliseconds |
| error | TEXT | Error message |
| decision | TEXT | Decision (accept/reject) |
| source | TEXT | Decision source |
| tool_parameters | TEXT | Tool parameters as JSON |
| model | TEXT | Claude model used |
| cost_usd | REAL | Cost in USD |
| input_tokens | INTEGER | Input tokens |
| output_tokens | INTEGER | Output tokens |
| cache_read_tokens | INTEGER | Cache read tokens |
| cache_creation_tokens | INTEGER | Cache creation tokens |
| status_code | INTEGER | HTTP status code |
| attempt | INTEGER | Attempt number |
| custom_attributes | TEXT | Additional attributes as JSON |

## Customization

### Creating Custom Grafana Dashboards

1. Access Grafana at http://localhost:3000
2. Click "+" → "Dashboard"
3. Add panels using SQL queries against the SQLite datasource
4. Example query:
   ```sql
   SELECT
     timestamp,
     SUM(metric_value) as total_tokens
   FROM metrics
   WHERE metric_name = 'claude_code.token.usage'
     AND type = 'input'
   GROUP BY strftime('%Y-%m-%d %H', timestamp)
   ORDER BY timestamp
   ```

### Modifying the SQLite Bridge

Edit `sqlite-bridge/app.py` to:
- Add custom processing logic
- Create aggregated views
- Add additional API endpoints
- Integrate with other systems

After modifications:
```bash
docker-compose up -d --build sqlite-bridge
```

## Contributing

Suggestions and improvements are welcome! Key areas for enhancement:
- Additional Grafana dashboard panels
- Data retention policies
- Alert configurations
- Integration with other monitoring systems

## License

This project is provided as-is for monitoring Claude Code usage.

## Support

For Claude Code issues: https://github.com/anthropics/claude-code/issues
For this monitoring setup: Create an issue in your project repository

## Acknowledgments

- Built with OpenTelemetry for standardized telemetry
- Grafana for visualization
- SQLite for lightweight, portable storage
