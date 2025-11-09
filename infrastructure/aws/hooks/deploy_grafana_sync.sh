#!/usr/bin/env bash
#
# infrastructure/aws/hooks/deploy_grafana_sync.sh
# Sync Grafana dashboards & alerts to production Lightsail Grafana container
#

set -e

# ----------------------------------------------------------------------
# Environment Variables (provided by Lightsail or CI/CD)
# ----------------------------------------------------------------------
GRAFANA_URL=${GRAFANA_URL:-"https://grafana.freelancer.io"}
GRAFANA_USER=${GRAFANA_USER:-"admin"}
GRAFANA_PASS=${GRAFANA_PASS:-$GRAFANA_ADMIN_PASS}
DASHBOARD_DIR=${DASHBOARD_DIR:-"infrastructure/monitoring/grafana/dashboards"}
ALERTING_FILE=${ALERTING_FILE:-"infrastructure/monitoring/grafana/alerting/alerting.yaml"}

echo "🚀 Starting Grafana synchronization hook for Lightsail deployment..."

# ----------------------------------------------------------------------
# Health Check
# ----------------------------------------------------------------------
echo "⏳ Checking Grafana health..."
for i in {1..30}; do
  if curl -s -u "$GRAFANA_USER:$GRAFANA_PASS" "$GRAFANA_URL/api/health" | grep -q "OK"; then
    echo "✅ Grafana is healthy."
    break
  fi
  echo "Waiting for Grafana to become available..."
  sleep 5
done

# ----------------------------------------------------------------------
# Import Dashboards
# ----------------------------------------------------------------------
echo "📥 Importing dashboards from $DASHBOARD_DIR..."
for dashboard in $DASHBOARD_DIR/*.json; do
  [ -e "$dashboard" ] || continue
  echo "→ Importing $(basename "$dashboard")..."
  curl -s -X POST "$GRAFANA_URL/api/dashboards/db" \
    -u "$GRAFANA_USER:$GRAFANA_PASS" \
    -H "Content-Type: application/json" \
    -d @\"$dashboard\" >/dev/null 2>&1 \
    && echo "✅ Imported $(basename "$dashboard")" \
    || echo "⚠️ Failed to import $(basename "$dashboard")"
done

# ----------------------------------------------------------------------
# Sync Alerting Configuration
# ----------------------------------------------------------------------
if [ -f "$ALERTING_FILE" ]; then
  echo "🔔 Syncing alerting configuration..."
  curl -s -X POST "$GRAFANA_URL/api/v1/provisioning/contact-points" \
    -u "$GRAFANA_USER:$GRAFANA_PASS" \
    -H "Content-Type: application/yaml" \
    --data-binary @"$ALERTING_FILE" >/dev/null 2>&1 \
    && echo "✅ Alerts configuration synced."
else
  echo "⚠️ No alerting file found; skipping alerts sync."
fi

echo "🎉 Grafana sync complete for Lightsail deployment."