"""Public, machine-readable contracts for supervised evaluation runs."""
from __future__ import annotations

from enum import StrEnum


class RunPhase(StrEnum):
    PREPARED = "prepared"
    SERVER_STARTING = "server_starting"
    READY = "ready"
    AUTONOMOUS = "autonomous"
    SUPERVISED_RECOVERY = "supervised_recovery"
    TERMINAL = "terminal"


class TerminalClass(StrEnum):
    ACCEPTED = "accepted"
    MODEL_UNRECOVERABLE = "model_unrecoverable"
    MODEL_DESTRUCTIVE = "model_destructive"
    INFRASTRUCTURE_BLOCKED = "infrastructure_blocked"
    HARNESS_BLOCKED = "harness_blocked"
    SERVER_COMPATIBILITY_BLOCKED = "server_compatibility_blocked"
    OPERATOR_STOPPED = "operator_stopped"


class InterventionClass(StrEnum):
    I0_INFRASTRUCTURE = "I0_infrastructure"
    I1_DIAGNOSTIC = "I1_diagnostic"
    I2_CRITERION_REMINDER = "I2_criterion_reminder"
    I3_DIRECTIONAL_HINT = "I3_directional_hint"
    I4_IMPLEMENTATION_FORBIDDEN = "I4_implementation_forbidden"


ALLOWED_TRANSITIONS = {
    RunPhase.PREPARED: {RunPhase.SERVER_STARTING, RunPhase.TERMINAL},
    RunPhase.SERVER_STARTING: {RunPhase.READY, RunPhase.TERMINAL},
    RunPhase.READY: {RunPhase.AUTONOMOUS, RunPhase.TERMINAL},
    RunPhase.AUTONOMOUS: {RunPhase.SUPERVISED_RECOVERY, RunPhase.TERMINAL},
    RunPhase.SUPERVISED_RECOVERY: {RunPhase.TERMINAL},
    RunPhase.TERMINAL: set(),
}


def transition_is_valid(current: RunPhase, target: RunPhase) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
