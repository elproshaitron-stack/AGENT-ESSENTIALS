"""Memory Engine: save, retrieve, summarize and pack context within a budget."""

from __future__ import annotations

from agent_essentials import MemoryEngine


def main() -> None:
    mem = MemoryEngine()
    mem.save_memory("User prefers dark mode and concise answers.", importance=0.8)
    mem.save_memory("User is building a sports-league SaaS in Mexico.", importance=0.9)
    mem.save_memory("The deployment runs on Cloud Run with a Postgres database.")
    mem.save_memory("User dislikes long, rambling explanations.", importance=0.7)

    print("Retrieval for 'what does the user like?':")
    for hit in mem.retrieve_memory("what does the user like?", k=3):
        print(f"  [{hit.score:.3f}] {hit.content}")

    print("\nSummary of everything stored:")
    print(" ", mem.summarize_memory(max_sentences=2))

    print("\nContext packed into a 40-token budget:")
    ctx = mem.optimize_context("user preferences", token_budget=40)
    print(
        f"  used {ctx.used_tokens}/{ctx.token_budget} tokens, "
        f"{len(ctx.included)} included, {ctx.summarized_count} summarized, "
        f"{ctx.dropped_count} dropped"
    )
    print(" ", ctx.context.replace("\n", "\n  "))


if __name__ == "__main__":
    main()
