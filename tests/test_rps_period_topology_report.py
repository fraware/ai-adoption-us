from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_period_topology_report_is_metadata_only_and_live_workflow_runs_it() -> None:
    script = (ROOT / "scripts" / "report_rps_period_topology.py").read_text()
    workflow = (ROOT / ".github" / "workflows" / "rps-live-validation.yml").read_text()

    assert '"diagnostic_type": "rps_series_period_topology_metadata_only"' in script
    assert '"raw_observation_values_included": False' in script
    assert '"subgroup_period_shapes"' in script
    assert '"national_period_shapes"' in script
    assert '"subgroup_common_periods"' in script
    assert '"subgroup_series_count_by_period"' in script
    assert 'row.get("value")' not in script
    assert 'observation.get("value")' not in script
    assert "realtime_start" not in script
    assert "realtime_end" not in script
    assert "source_last_updated" not in script

    assert "scripts/report_rps_period_topology.py" in workflow
    assert "Report rights-safe RPS period topology" in workflow
    retrieve = workflow.index("Retrieve and validate live RPS aggregate source")
    topology = workflow.index("Report rights-safe RPS period topology")
    candidate = workflow.index("Build non-promoting RPS observatory component")
    assert retrieve < topology < candidate
