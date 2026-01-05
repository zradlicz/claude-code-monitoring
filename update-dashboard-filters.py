#!/usr/bin/env python3
"""
Script to add filter variables to all panel queries in the Grafana dashboard
"""
import json
import re

DASHBOARD_FILE = 'grafana/provisioning/dashboards/claude-code-dashboard.json'

# Filter clause to add to WHERE conditions
FILTER_CLAUSE = " AND ('$hostname' = 'All' OR json_extract(custom_attributes, '$.host.name') = '$hostname') AND ('$project' = 'All' OR json_extract(custom_attributes, '$.project.name') = '$project') AND ('$session_id' = 'All' OR session_id = '$session_id')"

def add_filters_to_query(query):
    """Add filter variables to a SQL query if not already present"""
    if not query or '$hostname' in query:
        return query  # Already has filters

    # Find WHERE clause
    where_match = re.search(r'\bWHERE\b', query, re.IGNORECASE)
    if not where_match:
        return query  # No WHERE clause, skip

    # Find ORDER BY, GROUP BY, or LIMIT to insert before them
    insert_before = re.search(r'\b(ORDER BY|GROUP BY|LIMIT)\b', query, re.IGNORECASE)

    if insert_before:
        # Insert filter before ORDER BY/GROUP BY/LIMIT
        pos = insert_before.start()
        return query[:pos] + FILTER_CLAUSE + ' ' + query[pos:]
    else:
        # Append to end
        return query + FILTER_CLAUSE

def update_dashboard():
    """Update all panel queries in the dashboard"""
    with open(DASHBOARD_FILE, 'r') as f:
        dashboard = json.load(f)

    panels_updated = 0

    # Iterate through all panels
    for panel in dashboard.get('panels', []):
        if 'targets' not in panel:
            continue

        for target in panel['targets']:
            # Update queryText
            if 'queryText' in target:
                original = target['queryText']
                updated = add_filters_to_query(original)
                if updated != original:
                    target['queryText'] = updated
                    panels_updated += 1

            # Update rawQueryText (should match queryText)
            if 'rawQueryText' in target:
                original = target['rawQueryText']
                updated = add_filters_to_query(original)
                if updated != original:
                    target['rawQueryText'] = updated

    # Write back
    with open(DASHBOARD_FILE, 'w') as f:
        json.dump(dashboard, f, indent=2)

    print(f"Updated {panels_updated} panel queries with filter variables")
    return panels_updated

if __name__ == '__main__':
    update_dashboard()
