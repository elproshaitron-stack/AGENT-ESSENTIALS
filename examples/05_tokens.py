"""Token Counter: estimate cost and compare models for the same workload."""

from __future__ import annotations

from agent_essentials import TokenCounter


def main() -> None:
    tc = TokenCounter()

    est = tc.estimate_cost(
        model="claude-sonnet-4-6", input_tokens=1_500, output_tokens=500, requests=100_000
    )
    print(
        f"{est.model}: 100k requests => ${est.total_cost:,.2f} "
        f"(in ${est.input_cost:,.2f} / out ${est.output_cost:,.2f})"
    )
    print("Suggestions:")
    for s in est.suggestions:
        print(f"  - [{s.priority.value}] {s.title}: {s.detail}")

    print("\nSame workload across all models (cheapest first):")
    comparison = tc.compare(input_tokens=1_500, output_tokens=500, requests=100_000)
    for row in comparison.ranked:
        print(f"  ${row['total_cost']:>10,.2f}  {row['model']} ({row['provider']})")


if __name__ == "__main__":
    main()
