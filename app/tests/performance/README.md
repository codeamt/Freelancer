# Freelancer App Performance Testing (Distributed Mode)

## Overview

This directory includes **Locust-based distributed load testing** for FastApp modules:

- Authentication
- Commerce (Stripe + checkout)
- Learning Management (LMS)
- Social Network interactions

## Run in Standalone Mode

```bash
uv run locust -f tests/performance/locustfile.py --host http://localhost:8000
```

## Run Distributed via Docker Compose

```bash
docker compose -f tests/performance/docker-compose.locust.yml up --scale locust-worker=4
```

Access the Locust web UI at [http://localhost:8089](http://localhost:8089)

## Metrics Captured

- Average response time per route
- Request success/failure ratios
- Throughput (req/s)
- Latency distribution

## Recommended Scenarios

- 100 users for 2 minutes (smoke test)
- 1000 users ramp-up for 10 minutes (stress test)
- 2000+ sustained users for soak testing

## Scaling

- Add more workers with `--scale locust-worker=n`
- Adjust the number of concurrent users and spawn rate in the web UI or CLI
