#!/usr/bin/env python3
"""
scripts/import_grafana_dashboards.py
Automates Grafana dashboard import using Grafana REST API.
"""

import os
import time
import json
import requests

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASS = os.getenv("GRAFANA_PASS", "admin")
DASHBOARD_DIR = os.getenv(
    "GRAFANA_DASHBOARD_DIR", "infrastructure/monitoring/grafana/dashboards"
)

def grafana_ready(timeout=120):
    """Wait until Grafana API is available."""
    print("⏳ Waiting for Grafana to become available...")
    for _ in range(timeout):
        try:
            resp = requests.get(f"{GRAFANA_URL}/api/health")
            if resp.status_code == 200:
                print("✅ Grafana is ready.")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("❌ Grafana did not become ready in time.")
    return False


def import_dashboard(file_path):
    """Import a single dashboard JSON file."""
    with open(file_path, "r") as f:
        dashboard_json = json.load(f)

    payload = {
        "dashboard": dashboard_json.get("dashboard", dashboard_json),
        "overwrite": True,
        "folderId": 0
    }

    resp = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        json=payload
    )

    if resp.status_code in (200, 201):
        print(f"✅ Imported: {os.path.basename(file_path)}")
    else:
        print(f"⚠️ Failed to import {file_path}: {resp.status_code} {resp.text}")


def main():
    if not grafana_ready():
        exit(1)

    print(f"📁 Importing dashboards from: {DASHBOARD_DIR}")
    if not os.path.isdir(DASHBOARD_DIR):
        print(f"❌ Dashboard directory not found: {DASHBOARD_DIR}")
        exit(1)

    dashboards = [
        os.path.join(DASHBOARD_DIR, f)
        for f in os.listdir(DASHBOARD_DIR)
        if f.endswith(".json")
    ]

    if not dashboards:
        print("⚠️ No dashboards found to import.")
        exit(0)

    for dashboard_file in dashboards:
        import_dashboard(dashboard_file)

    print("🎉 Dashboard import process completed successfully!")


if __name__ == "__main__":
    main()