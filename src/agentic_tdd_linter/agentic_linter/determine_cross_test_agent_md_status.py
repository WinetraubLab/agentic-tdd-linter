"""Determine whether an agent completed a cross-test review packet."""

from __future__ import annotations

from .determine_agent_md_status import determine_agent_md_status


def determine_cross_test_agent_md_status(artifact_text: str) -> str:
    """Return pending, pass, or fail from a cross-test review scorecard."""

    return determine_agent_md_status(artifact_text)
