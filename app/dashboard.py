"""Streamlit dashboard backed by data/logs.jsonl and config/dashboard.yaml."""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import altair as alt
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"
LOG_PATH = ROOT / "data" / "logs.jsonl"


def load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def parse_ts(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


@st.cache_data(ttl=30)
def load_events(path: str, cutoff_iso: str) -> list[dict[str, Any]]:
    cutoff = datetime.fromisoformat(cutoff_iso)
    source = Path(path)
    if not source.exists():
        return []
    events = []
    for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        timestamp = parse_ts(event.get("ts"))
        if timestamp and timestamp >= cutoff:
            events.append(event)
    return events


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, math.ceil(p * len(ordered) / 100) - 1))]


def minute(event: dict[str, Any]) -> str:
    timestamp = parse_ts(event.get("ts"))
    return timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M") if timestamp else "unknown"


def chart(rows: list[dict[str, Any]], value: str, title: str, unit: str, threshold: dict[str, Any]) -> None:
    if not rows:
        st.info("No data in the selected 60-minute window.")
        return
    line = alt.Chart(alt.Data(values=rows)).mark_line(point=True).encode(
        x=alt.X("minute:N", title="UTC minute", sort=None),
        y=alt.Y(f"{value}:Q", title=f"{title} ({unit})"),
        tooltip=["minute:N", f"{value}:Q"],
    ).properties(height=220)
    rule = alt.Chart(alt.Data(values=[{"limit": threshold["value"]}])).mark_rule(
        color="red", strokeDash=[5, 5]
    ).encode(y="limit:Q", tooltip=alt.value(f"threshold {threshold['operator']} {threshold['value']} {unit}"))
    st.altair_chart(line + rule, use_container_width=True)


def multi_chart(
    rows: list[dict[str, Any]],
    fields: list[str],
    title: str,
    unit: str,
    threshold: dict[str, Any] | None = None,
) -> None:
    """Render a time-series chart from values loaded from the real JSONL log."""
    if not rows:
        st.info("No data in the selected 60-minute window.")
        return
    values = alt.Chart(alt.Data(values=rows)).transform_fold(fields, as_=["metric", "value"])
    line = values.mark_line(point=True).encode(
        x=alt.X("minute:N", title="UTC minute", sort=None),
        y=alt.Y("value:Q", title=f"{title} ({unit})"),
        color=alt.Color("metric:N", title="Metric"),
        tooltip=["minute:N", "metric:N", "value:Q"],
    ).properties(height=220)
    if threshold is None:
        st.altair_chart(line, use_container_width=True)
        return
    rule = alt.Chart(alt.Data(values=[{"limit": threshold["value"]}])).mark_rule(
        color="red", strokeDash=[5, 5]
    ).encode(
        y="limit:Q",
        tooltip=alt.value(f"threshold {threshold['operator']} {threshold['value']} {unit}"),
    )
    st.altair_chart(line + rule, use_container_width=True)


def main() -> None:
    config = load_config()["dashboard"]
    panels = {panel["id"]: panel for panel in config["panels"]}
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=config["time_range_minutes"])
    st.set_page_config(page_title=config["title"], layout="wide")
    st.title(config["title"])
    st.caption(f"Last {config['time_range_minutes']} minutes · UTC · refresh every {config['refresh_seconds']} seconds")
    events = load_events(str(LOG_PATH), cutoff.isoformat())
    responses = [e for e in events if e.get("event") == "response_sent"]
    requests = [e for e in events if e.get("event") == "request_received"]
    failures = [e for e in events if e.get("event") == "request_failed"]

    left, right = st.columns(2)
    with left:
        st.subheader("Latency")
        latencies = [float(e["latency_ms"]) for e in responses if "latency_ms" in e]
        ttft = [float(e["ttft_ms"]) for e in responses if "ttft_ms" in e]
        st.metric("P50 / P95 / P99", f"{percentile(latencies,50):.0f} / {percentile(latencies,95):.0f} / {percentile(latencies,99):.0f} ms")
        st.metric("TTFT P95", f"{percentile(ttft,95):.0f} ms")
        chart([{ "minute": minute(e), "latency_ms": e["latency_ms"] } for e in responses if "latency_ms" in e], "latency_ms", panels["latency"]["title"], "ms", panels["latency"]["threshold"])
    with right:
        st.subheader("Traffic")
        traffic: dict[str, int] = {}
        for event in requests:
            traffic[minute(event)] = traffic.get(minute(event), 0) + 1
        st.metric("Requests", len(requests))
        st.metric("Average rate", f"{len(requests) / config['time_range_minutes']:.2f} requests/min")
        chart([{ "minute": key, "requests_per_minute": value } for key, value in sorted(traffic.items())], "requests_per_minute", panels["traffic"]["title"], "requests/min", panels["traffic"]["threshold"])

    left, right = st.columns(2)
    with left:
        st.subheader("Errors")
        tool_events = [e for e in events if e.get("tool_success") is not None]
        retrieval = 100 * sum(e.get("tool_success") is True for e in tool_events) / len(tool_events) if tool_events else 0
        error_rate = 100 * len(failures) / len(requests) if requests else 0
        st.metric("Error rate", f"{error_rate:.2f}%")
        st.metric("Retrieval success", f"{retrieval:.2f}%")
        st.caption(f"Error threshold: {panels['errors']['threshold']['operator']} {panels['errors']['threshold']['value']}%")
        st.write("Error breakdown", {str(kind): sum(e.get("error_type") == kind for e in failures) for kind in {e.get("error_type") for e in failures}})
    with right:
        st.subheader("Cost")
        costs: dict[str, float] = {}
        for event in responses:
            if "cost_usd" in event:
                costs[minute(event)] = costs.get(minute(event), 0.0) + float(event["cost_usd"])
        rows = [{"minute": key, "cost_usd": value} for key, value in sorted(costs.items())]
        st.metric("Total cost", f"${sum(float(row['cost_usd']) for row in rows):.4f}")
        chart(rows, "cost_usd", panels["cost"]["title"], "USD", panels["cost"]["threshold"])

    left, right = st.columns(2)
    with left:
        st.subheader("Tokens")
        total_in = sum(int(e.get("tokens_in", 0)) for e in responses)
        total_out = sum(int(e.get("tokens_out", 0)) for e in responses)
        st.metric("Input tokens", f"{total_in:,}")
        st.metric("Output tokens", f"{total_out:,}")
        st.caption(f"Threshold: {panels['tokens']['threshold']['operator']} {panels['tokens']['threshold']['value']:,} tokens")
        multi_chart(
            [
                {
                    "minute": minute(event),
                    "tokens_in": int(event.get("tokens_in", 0)),
                    "tokens_out": int(event.get("tokens_out", 0)),
                }
                for event in responses
            ],
            ["tokens_in", "tokens_out"],
            panels["tokens"]["title"],
            "tokens",
            panels["tokens"]["threshold"],
        )
    with right:
        st.subheader("Quality")
        scores = [float(e["quality_score"]) for e in responses if "quality_score" in e]
        average = sum(scores) / len(scores) if scores else 0
        st.metric("Quality proxy mean", f"{average:.3f}")
        st.caption(f"Threshold: {panels['quality']['threshold']['operator']} {panels['quality']['threshold']['value']}")
        st.progress(min(1.0, average))
        chart(
            [
                {"minute": minute(event), "quality_score": float(event["quality_score"])}
                for event in responses
                if "quality_score" in event
            ],
            "quality_score",
            panels["quality"]["title"],
            "score_0_to_1",
            panels["quality"]["threshold"],
        )


if __name__ == "__main__":
    main()
