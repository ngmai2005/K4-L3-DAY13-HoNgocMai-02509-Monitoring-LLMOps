# Alert Runbooks

All alerts use Metrics -> Logs -> Traces.

## Alert 1

- Name: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Slack channel: `#k4-l3b-alerts`
- Condition: `p95(response_sent.latency_ms) > 3000ms` for 5 minutes
- Impact: responses exceed the 3-second target.
- Checks: latency panel -> high-latency `correlation_id` in JSONL -> Langfuse trace.
- Mitigation: rollback the prompt or disable the latency-causing incident.
- Owner: `student-<MSSV>`

## Alert 2

- Name: `ElevatedErrorRate`
- Severity: `critical`
- Duration: `5m`
- Slack channel: `#k4-l3b-alerts`
- Condition: `request_failed / request_received > 2%` for 5 minutes
- Impact: requests fail without an answer.
- Checks: errors panel -> `error_type` and `tool_success` -> matching trace.
- Mitigation: disable the incident, rollback the prompt, or reduce traffic.
- Owner: `student-<MSSV>`

## Alert 3

- Name: `LowRetrievalSuccess`
- Severity: `warning`
- Duration: `5m`
- Slack channel: `#k4-l3b-alerts`
- Condition: `tool_success == true / tool_success != null < 90%` for 5 minutes
- Impact: answers may miss relevant context or use fallback content.
- Checks: retrieval panel -> JSONL `tool_name`/`tool_success` -> retrieval span.
- Mitigation: disable the retrieval incident and restore the vector-store dependency.
- Owner: `student-<MSSV>`
