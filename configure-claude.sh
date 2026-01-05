#!/bin/bash

# Claude Code Monitoring Configuration Script
# This script helps set up environment variables for Claude Code telemetry

echo "========================================="
echo "Claude Code Telemetry Configuration"
echo "========================================="
echo ""

# Check if running on the same machine or remote
read -p "Are you running Claude Code on this same machine? (y/n): " SAME_MACHINE

if [ "$SAME_MACHINE" = "y" ]; then
    COLLECTOR_ENDPOINT="http://localhost:4317"
else
    read -p "Enter the IP address or hostname of your monitoring server: " SERVER_HOST
    COLLECTOR_ENDPOINT="http://${SERVER_HOST}:4317"
fi

echo ""
echo "========================================="
echo "Configuration for Claude Code"
echo "========================================="
echo ""
echo "Add these environment variables to your shell configuration"
echo "(~/.bashrc, ~/.zshrc, or similar):"
echo ""
echo "# Claude Code Monitoring"
echo "export CLAUDE_CODE_ENABLE_TELEMETRY=1"
echo "export OTEL_METRICS_EXPORTER=otlp"
echo "export OTEL_LOGS_EXPORTER=otlp"
echo "export OTEL_EXPORTER_OTLP_PROTOCOL=grpc"
echo "export OTEL_EXPORTER_OTLP_ENDPOINT=${COLLECTOR_ENDPOINT}"
echo ""
echo "# IMPORTANT: Enable user prompt capture (contains sensitive data)"
echo "export OTEL_LOG_USER_PROMPTS=1"
echo ""
echo "# Optional: Faster export intervals for testing (default is 60s for metrics)"
echo "# export OTEL_METRIC_EXPORT_INTERVAL=10000  # 10 seconds"
echo "# export OTEL_LOGS_EXPORT_INTERVAL=5000     # 5 seconds"
echo ""
echo "# Optional: Add custom attributes for organization/team tracking"
echo "# export OTEL_RESOURCE_ATTRIBUTES=\"department=engineering,team=platform\""
echo ""
echo "========================================="
echo ""
echo "After adding these to your shell config, run:"
echo "  source ~/.bashrc  (or ~/.zshrc)"
echo ""
echo "Or set them temporarily for the current session:"
echo "  export CLAUDE_CODE_ENABLE_TELEMETRY=1"
echo "  export OTEL_METRICS_EXPORTER=otlp"
echo "  export OTEL_LOGS_EXPORTER=otlp"
echo "  export OTEL_EXPORTER_OTLP_PROTOCOL=grpc"
echo "  export OTEL_EXPORTER_OTLP_ENDPOINT=${COLLECTOR_ENDPOINT}"
echo "  export OTEL_LOG_USER_PROMPTS=1"
echo ""
echo "Then run Claude Code as normal: claude"
echo ""

# Offer to create a temporary file
read -p "Would you like to save these to a file? (y/n): " SAVE_FILE

if [ "$SAVE_FILE" = "y" ]; then
    OUTPUT_FILE="claude-code-env.sh"
    cat > "$OUTPUT_FILE" << EOF
#!/bin/bash
# Claude Code Monitoring Configuration
# Source this file before running Claude Code: source ./claude-code-env.sh

export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=${COLLECTOR_ENDPOINT}

# IMPORTANT: This will capture your prompts (sensitive data)
export OTEL_LOG_USER_PROMPTS=1

# Optional: Faster export intervals for testing
# export OTEL_METRIC_EXPORT_INTERVAL=10000
# export OTEL_LOGS_EXPORT_INTERVAL=5000

# Optional: Custom attributes
# export OTEL_RESOURCE_ATTRIBUTES="department=engineering,team=platform"
EOF
    chmod +x "$OUTPUT_FILE"
    echo ""
    echo "Configuration saved to: $OUTPUT_FILE"
    echo "To use it, run: source ./$OUTPUT_FILE"
    echo ""
fi

echo "========================================="
echo "Privacy & Security Notes:"
echo "========================================="
echo ""
echo "⚠️  IMPORTANT: OTEL_LOG_USER_PROMPTS=1 will capture ALL your"
echo "    prompts to Claude Code. This includes potentially sensitive"
echo "    information like code, credentials, or private data."
echo ""
echo "    Only enable this if:"
echo "    - You control the monitoring infrastructure"
echo "    - You understand the privacy implications"
echo "    - You have proper data handling policies in place"
echo ""
echo "    Without this flag, only prompt LENGTH is recorded,"
echo "    not the actual content."
echo ""
