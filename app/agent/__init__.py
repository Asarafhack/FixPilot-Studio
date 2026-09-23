"""
FixPilot Studio agent package.

The public diagnose_error() function is exposed through a lazy
wrapper to avoid circular imports between the agent and repair
planner modules.
"""


def diagnose_error(error):
    """
    Lazily import and call the diagnostician.

    The lazy import prevents this cycle:

        app.agent
            ↓
        diagnostician
            ↓
        repair.planner
            ↓
        app.agent

    while preserving the existing public API:

        from app.agent import diagnose_error
    """

    from .diagnostician import diagnose_error as _diagnose_error

    return _diagnose_error(error)


__all__ = ["diagnose_error"]