#!/usr/bin/env python3
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
import logging
from pathlib import Path

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = '/data/claude_monitoring.db'

def init_db():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            session_id TEXT,
            account_uuid TEXT,
            organization_id TEXT,
            terminal_type TEXT,
            app_version TEXT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metric_unit TEXT,
            model TEXT,
            type TEXT,
            tool TEXT,
            decision TEXT,
            language TEXT,
            custom_attributes TEXT,
            INDEX idx_timestamp (timestamp),
            INDEX idx_session_id (session_id),
            INDEX idx_metric_name (metric_name)
        )
    ''')

    # Events/Logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            session_id TEXT,
            account_uuid TEXT,
            organization_id TEXT,
            terminal_type TEXT,
            app_version TEXT,
            event_name TEXT NOT NULL,
            prompt TEXT,
            prompt_length INTEGER,
            tool_name TEXT,
            success TEXT,
            duration_ms INTEGER,
            error TEXT,
            decision TEXT,
            source TEXT,
            tool_parameters TEXT,
            model TEXT,
            cost_usd REAL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cache_read_tokens INTEGER,
            cache_creation_tokens INTEGER,
            status_code INTEGER,
            attempt INTEGER,
            custom_attributes TEXT,
            INDEX idx_timestamp (timestamp),
            INDEX idx_session_id (session_id),
            INDEX idx_event_name (event_name)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")

def extract_common_attributes(resource_attributes, scope_attributes=None):
    """Extract common attributes from resource and scope."""
    attrs = {}

    all_attrs = list(resource_attributes) if resource_attributes else []
    if scope_attributes:
        all_attrs.extend(scope_attributes)

    for attr in all_attrs:
        key = attr.get('key', '')
        value = attr.get('value', {})

        # Extract value based on type
        if 'stringValue' in value:
            val = value['stringValue']
        elif 'intValue' in value:
            val = value['intValue']
        elif 'doubleValue' in value:
            val = value['doubleValue']
        elif 'boolValue' in value:
            val = value['boolValue']
        else:
            val = str(value)

        attrs[key] = val

    return attrs

def store_metrics(metrics_data):
    """Store metrics in SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    count = 0
    for resource_metric in metrics_data.get('resourceMetrics', []):
        resource_attrs = extract_common_attributes(
            resource_metric.get('resource', {}).get('attributes', [])
        )

        for scope_metric in resource_metric.get('scopeMetrics', []):
            for metric in scope_metric.get('metrics', []):
                metric_name = metric.get('name', '')

                # Handle different metric types
                data_points = []
                metric_unit = metric.get('unit', '')

                if 'sum' in metric:
                    data_points = metric['sum'].get('dataPoints', [])
                elif 'gauge' in metric:
                    data_points = metric['gauge'].get('dataPoints', [])
                elif 'histogram' in metric:
                    data_points = metric['histogram'].get('dataPoints', [])

                for point in data_points:
                    # Extract value
                    value = point.get('asDouble', point.get('asInt', 0))

                    # Extract timestamp (nanoseconds to datetime)
                    ts_nanos = point.get('timeUnixNano', 0)
                    timestamp = datetime.fromtimestamp(ts_nanos / 1e9) if ts_nanos else datetime.now()

                    # Extract point attributes
                    point_attrs = extract_common_attributes(point.get('attributes', []))

                    # Combine all attributes
                    all_attrs = {**resource_attrs, **point_attrs}

                    cursor.execute('''
                        INSERT INTO metrics (
                            timestamp, session_id, account_uuid, organization_id,
                            terminal_type, app_version, metric_name, metric_value,
                            metric_unit, model, type, tool, decision, language,
                            custom_attributes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        timestamp,
                        all_attrs.get('session.id'),
                        all_attrs.get('user.account_uuid'),
                        all_attrs.get('organization.id'),
                        all_attrs.get('terminal.type'),
                        all_attrs.get('app.version'),
                        metric_name,
                        value,
                        metric_unit,
                        all_attrs.get('model'),
                        all_attrs.get('type'),
                        all_attrs.get('tool'),
                        all_attrs.get('decision'),
                        all_attrs.get('language'),
                        json.dumps({k: v for k, v in all_attrs.items()
                                   if k not in ['session.id', 'user.account_uuid',
                                               'organization.id', 'terminal.type',
                                               'app.version', 'model', 'type', 'tool',
                                               'decision', 'language']})
                    ))
                    count += 1

    conn.commit()
    conn.close()
    return count

def store_logs(logs_data):
    """Store logs/events in SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    count = 0
    for resource_log in logs_data.get('resourceLogs', []):
        resource_attrs = extract_common_attributes(
            resource_log.get('resource', {}).get('attributes', [])
        )

        for scope_log in resource_log.get('scopeLogs', []):
            for log_record in scope_log.get('logRecords', []):
                # Extract timestamp
                ts_nanos = log_record.get('timeUnixNano', 0)
                timestamp = datetime.fromtimestamp(ts_nanos / 1e9) if ts_nanos else datetime.now()

                # Extract log attributes
                log_attrs = extract_common_attributes(log_record.get('attributes', []))

                # Combine all attributes
                all_attrs = {**resource_attrs, **log_attrs}

                # Determine event name from log body or attributes
                event_name = log_record.get('body', {}).get('stringValue',
                            all_attrs.get('event.name', 'unknown_event'))

                cursor.execute('''
                    INSERT INTO events (
                        timestamp, session_id, account_uuid, organization_id,
                        terminal_type, app_version, event_name, prompt,
                        prompt_length, tool_name, success, duration_ms,
                        error, decision, source, tool_parameters, model,
                        cost_usd, input_tokens, output_tokens, cache_read_tokens,
                        cache_creation_tokens, status_code, attempt, custom_attributes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    all_attrs.get('session.id'),
                    all_attrs.get('user.account_uuid'),
                    all_attrs.get('organization.id'),
                    all_attrs.get('terminal.type'),
                    all_attrs.get('app.version'),
                    event_name,
                    all_attrs.get('prompt'),
                    all_attrs.get('prompt_length'),
                    all_attrs.get('tool_name'),
                    all_attrs.get('success'),
                    all_attrs.get('duration_ms'),
                    all_attrs.get('error'),
                    all_attrs.get('decision'),
                    all_attrs.get('source'),
                    all_attrs.get('tool_parameters'),
                    all_attrs.get('model'),
                    all_attrs.get('cost_usd'),
                    all_attrs.get('input_tokens'),
                    all_attrs.get('output_tokens'),
                    all_attrs.get('cache_read_tokens'),
                    all_attrs.get('cache_creation_tokens'),
                    all_attrs.get('status_code'),
                    all_attrs.get('attempt'),
                    json.dumps({k: v for k, v in all_attrs.items()
                               if k not in ['session.id', 'user.account_uuid',
                                           'organization.id', 'terminal.type',
                                           'app.version', 'event.name', 'prompt',
                                           'prompt_length', 'tool_name', 'success',
                                           'duration_ms', 'error', 'decision', 'source',
                                           'tool_parameters', 'model', 'cost_usd',
                                           'input_tokens', 'output_tokens',
                                           'cache_read_tokens', 'cache_creation_tokens',
                                           'status_code', 'attempt']})
                ))
                count += 1

    conn.commit()
    conn.close()
    return count

@app.route('/v1/metrics', methods=['POST'])
def receive_metrics():
    """Receive metrics from OpenTelemetry collector."""
    try:
        data = request.get_json()
        count = store_metrics(data)
        logger.info(f"Stored {count} metric data points")
        return jsonify({"status": "success", "metrics_stored": count}), 200
    except Exception as e:
        logger.error(f"Error storing metrics: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/v1/logs', methods=['POST'])
def receive_logs():
    """Receive logs/events from OpenTelemetry collector."""
    try:
        data = request.get_json()
        count = store_logs(data)
        logger.info(f"Stored {count} log/event records")
        return jsonify({"status": "success", "logs_stored": count}), 200
    except Exception as e:
        logger.error(f"Error storing logs: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

@app.route('/stats', methods=['GET'])
def stats():
    """Get database statistics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM metrics')
        metrics_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM events')
        events_count = cursor.fetchone()[0]

        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM metrics')
        metric_range = cursor.fetchone()

        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM events')
        event_range = cursor.fetchone()

        conn.close()

        return jsonify({
            "metrics_count": metrics_count,
            "events_count": events_count,
            "metrics_time_range": {"start": metric_range[0], "end": metric_range[1]},
            "events_time_range": {"start": event_range[0], "end": event_range[1]}
        }), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Ensure data directory exists
    Path('/data').mkdir(exist_ok=True)

    # Initialize database
    init_db()

    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
