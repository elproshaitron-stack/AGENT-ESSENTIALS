"""Domain detection and the phase/task templates the planner expands.

The planner is deliberately template-driven: a stable SDLC skeleton plus
feature-gated tasks that switch on based on keywords detected in the goal. This
keeps output deterministic and explainable while still adapting to the request.

Detection is bilingual (English + Spanish) and accent-insensitive so that goals
written in Spanish are not under-analysed.
"""

from __future__ import annotations

import unicodedata

from ..core.result import Severity
from ..utilities.text import tokenize

# Domain detection: first matching domain wins (order matters).
DOMAIN_KEYWORDS: dict[str, frozenset[str]] = {
    "saas": frozenset(
        {"saas", "platform", "subscription", "tenant", "dashboard", "plataforma", "suscripcion"}
    ),
    "ml_ai": frozenset(
        {
            "ai",
            "agent",
            "llm",
            "rag",
            "model",
            "ml",
            "recommendation",
            "ia",
            "agente",
            "modelo",
            "recomendacion",
            "aprendizaje",
        }
    ),
    "ecommerce": frozenset(
        {
            "shop",
            "store",
            "ecommerce",
            "marketplace",
            "checkout",
            "cart",
            "tienda",
            "carrito",
            "compra",
            "compras",
            "mercado",
        }
    ),
    "mobile": frozenset({"mobile", "ios", "android", "app", "movil", "aplicacion"}),
    "data": frozenset(
        {
            "data",
            "analytics",
            "etl",
            "pipeline",
            "warehouse",
            "report",
            "datos",
            "analitica",
            "reporte",
            "informe",
        }
    ),
    "api": frozenset(
        {
            "api",
            "service",
            "backend",
            "integration",
            "webhook",
            "servicio",
            "servicios",
            "integracion",
        }
    ),
}

# Feature gates: presence of any keyword switches the feature (and its tasks) on.
FEATURE_KEYWORDS: dict[str, frozenset[str]] = {
    "auth": frozenset(
        {
            "user",
            "users",
            "account",
            "login",
            "auth",
            "signup",
            "member",
            "usuario",
            "usuarios",
            "cuenta",
            "cuentas",
            "registro",
            "sesion",
            "miembro",
            "miembros",
            "autenticacion",
        }
    ),
    "payments": frozenset(
        {
            "payment",
            "payments",
            "billing",
            "subscription",
            "stripe",
            "checkout",
            "pago",
            "pagos",
            "facturacion",
            "suscripcion",
            "cobro",
            "cobros",
            "tarjeta",
        }
    ),
    "realtime": frozenset(
        {
            "realtime",
            "live",
            "chat",
            "notification",
            "websocket",
            "stream",
            "vivo",
            "directo",
            "streaming",
            "transmision",
            "notificacion",
            "notificaciones",
        }
    ),
    "ai": frozenset(
        {
            "ai",
            "agent",
            "llm",
            "rag",
            "recommendation",
            "ml",
            "model",
            "ia",
            "agente",
            "agentes",
            "modelo",
            "modelos",
            "recomendacion",
        }
    ),
    "mobile": frozenset(
        {"mobile", "ios", "android", "app", "movil", "moviles", "aplicacion", "telefono"}
    ),
    "analytics": frozenset(
        {
            "analytics",
            "dashboard",
            "report",
            "metrics",
            "insights",
            "analitica",
            "analiticas",
            "panel",
            "paneles",
            "reporte",
            "reportes",
            "informe",
            "informes",
            "metricas",
            "tablero",
        }
    ),
    "scheduling": frozenset(
        {
            "schedule",
            "league",
            "tournament",
            "booking",
            "calendar",
            "match",
            "liga",
            "ligas",
            "torneo",
            "torneos",
            "calendario",
            "partido",
            "partidos",
            "horario",
            "horarios",
            "reserva",
            "reservas",
            "cita",
            "citas",
        }
    ),
    "multitenant": frozenset(
        {
            "tenant",
            "saas",
            "organization",
            "workspace",
            "platform",
            "inquilino",
            "organizacion",
            "empresa",
            "empresas",
            "plataforma",
        }
    ),
}

# Phase skeleton. Each task spec: (title, description, effort, feature_gate|None).
# A None gate means the task is always included.
PHASES: list[tuple[str, str, str, list[tuple[str, str, str, str | None]]]] = [
    (
        "m1",
        "Discovery & Requirements",
        "Lock scope, success metrics and constraints before building.",
        [
            (
                "Define scope and success metrics",
                "Goals, non-goals, KPIs, acceptance criteria.",
                "small",
                None,
            ),
            (
                "Identify users and core flows",
                "User personas and the critical user journeys.",
                "small",
                None,
            ),
            (
                "Map compliance and data requirements",
                "Privacy, residency and retention needs.",
                "small",
                None,
            ),
        ],
    ),
    (
        "m2",
        "Architecture & Design",
        "Choose the stack and design the system and data model.",
        [
            (
                "Design system architecture",
                "Services, data stores, scaling and deployment model.",
                "medium",
                None,
            ),
            (
                "Design data model and schema",
                "Entities, relationships, migrations strategy.",
                "medium",
                None,
            ),
            (
                "Design AI/agent architecture",
                "Model routing, memory, retrieval and guardrails.",
                "medium",
                "ai",
            ),
            (
                "Design tenancy and isolation model",
                "Per-tenant data isolation and access control.",
                "medium",
                "multitenant",
            ),
            (
                "Design API contracts",
                "Endpoints, payloads, versioning and error model.",
                "medium",
                "api",
            ),
        ],
    ),
    (
        "m3",
        "Core Implementation",
        "Build the foundational product surface.",
        [
            (
                "Set up project skeleton and CI",
                "Repo, environments, CI pipeline and linting.",
                "small",
                None,
            ),
            (
                "Implement core domain logic",
                "The primary product capability end to end.",
                "large",
                None,
            ),
            (
                "Implement authentication & accounts",
                "Signup, login, sessions and roles.",
                "medium",
                "auth",
            ),
            (
                "Implement scheduling engine",
                "Constraint-aware scheduling and conflict handling.",
                "large",
                "scheduling",
            ),
            (
                "Implement AI integration",
                "Model calls, prompts, retrieval and validation.",
                "large",
                "ai",
            ),
            (
                "Build mobile client",
                "Native or cross-platform client for core flows.",
                "large",
                "mobile",
            ),
        ],
    ),
    (
        "m4",
        "Integrations & Data",
        "Wire external systems and reporting.",
        [
            (
                "Integrate payments & billing",
                "Provider integration, webhooks, dunning.",
                "medium",
                "payments",
            ),
            (
                "Implement realtime layer",
                "Websockets/SSE, presence and fan-out.",
                "medium",
                "realtime",
            ),
            (
                "Build analytics & dashboards",
                "Event tracking, metrics store and dashboards.",
                "medium",
                "analytics",
            ),
            (
                "Build admin & back-office tools",
                "Operational tooling for support and config.",
                "medium",
                None,
            ),
        ],
    ),
    (
        "m5",
        "Testing & Hardening",
        "Make it reliable, secure and observable.",
        [
            (
                "Write automated test suite",
                "Unit, integration and end-to-end coverage.",
                "medium",
                None,
            ),
            ("Add observability", "Logging, metrics, tracing and alerting.", "medium", None),
            (
                "Security review & load test",
                "Threat model, pen-test pass and load testing.",
                "medium",
                None,
            ),
            (
                "Validate AI outputs",
                "Eval set, hallucination checks and guardrails.",
                "medium",
                "ai",
            ),
        ],
    ),
    (
        "m6",
        "Launch & Operations",
        "Ship and operate in production.",
        [
            (
                "Prepare deployment & rollback",
                "IaC, environments, blue/green or canary.",
                "medium",
                None,
            ),
            ("Write docs and runbooks", "User docs, API docs and on-call runbooks.", "small", None),
            (
                "Launch and monitor",
                "Staged rollout with monitoring and feedback loop.",
                "small",
                None,
            ),
        ],
    ),
]

# Feature -> risk template: (title, description, severity, likelihood, mitigation).
RISK_TEMPLATES: dict[str, tuple[str, str, Severity, str, str]] = {
    "payments": (
        "Payment & compliance failures",
        "Billing edge cases and PCI scope can cause revenue loss and legal exposure.",
        Severity.HIGH,
        "medium",
        "Use a PCI-compliant provider, handle webhooks idempotently, and test failure paths.",
    ),
    "realtime": (
        "Realtime scaling",
        "Websocket fan-out and presence are hard to scale and easy to get wrong.",
        Severity.MEDIUM,
        "medium",
        "Use a managed pub/sub layer, load-test connection counts, and degrade gracefully.",
    ),
    "ai": (
        "AI reliability & cost",
        "Hallucinations and unbounded token spend threaten trust and margins.",
        Severity.HIGH,
        "high",
        "Add output validation, an eval set, model routing and per-request token budgets.",
    ),
    "multitenant": (
        "Tenant data isolation",
        "Cross-tenant data leakage is a critical security failure.",
        Severity.CRITICAL,
        "medium",
        "Enforce tenant scoping at the query layer and add automated isolation tests.",
    ),
    "scheduling": (
        "Scheduling complexity",
        "Constraint-heavy scheduling explodes in complexity and edge cases.",
        Severity.MEDIUM,
        "high",
        "Model constraints explicitly, start with a solver/heuristic, and test conflict cases.",
    ),
}

# Risks that always apply.
BASELINE_RISKS: list[tuple[str, str, Severity, str, str]] = [
    (
        "Scope creep",
        "Unbounded scope is the most common cause of missed deadlines.",
        Severity.MEDIUM,
        "high",
        "Freeze an MVP scope, track changes explicitly, and defer non-essential work.",
    ),
    (
        "Underestimated testing & hardening",
        "Teams routinely under-budget the work to make software production-ready.",
        Severity.MEDIUM,
        "medium",
        "Budget testing/observability as first-class tasks, not an afterthought.",
    ),
]


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _normalized_tokens(goal: str) -> set[str]:
    return set(tokenize(_strip_accents(goal)))


def detect_domain(goal: str) -> str:
    tokens = _normalized_tokens(goal)
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if tokens & keywords:
            return domain
    return "general"


def detect_features(goal: str) -> list[str]:
    tokens = _normalized_tokens(goal)
    return [feature for feature, keywords in FEATURE_KEYWORDS.items() if tokens & keywords]


__all__ = [
    "BASELINE_RISKS",
    "DOMAIN_KEYWORDS",
    "FEATURE_KEYWORDS",
    "PHASES",
    "RISK_TEMPLATES",
    "detect_domain",
    "detect_features",
]
