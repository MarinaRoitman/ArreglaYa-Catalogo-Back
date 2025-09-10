def test_metrics_returns_text(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    content_type = r.headers.get("content-type", "")
    assert "text/plain" in content_type
    body = r.text
    assert "process_cpu_seconds_total" in body or "python_gc_objects_collected_total" in body
