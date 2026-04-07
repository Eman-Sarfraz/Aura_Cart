import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as pe


def draw_agent(ax, text, xy, bg_color):
    b = patches.FancyBboxPatch(
        (xy[0] - 0.4, xy[1] - 0.2),
        0.8,
        0.4,
        boxstyle="round,pad=0.1",
        ec="none",
        fc=bg_color,
        path_effects=[pe.SimpleLineShadow(), pe.Normal()],
    )
    ax.add_patch(b)
    ax.text(
        xy[0],
        xy[1],
        text,
        ha="center",
        va="center",
        color="white",
        fontsize=8,
        fontweight="bold",
    )


def draw_arrow(ax, xy_from, xy_to):
    ax.annotate(
        "",
        xy=xy_to,
        xycoords="data",
        xytext=xy_from,
        textcoords="data",
        arrowprops=dict(arrowstyle="->", color="black", lw=1.5, connectionstyle="arc3,rad=0.1"),
    )


def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_axis_off()
    ax.set_xlim(-1, 12)
    ax.set_ylim(-1, 7)

    draw_agent(ax, "User / React\nFrontend", (0, 4), "#0f766e")

    agents = [
        ("Agent 1\nPreference", (2, 4), "#2563eb"),
        ("Agent 2\nRetrieval", (4, 4), "#1d4ed8"),
        ("Agent 3\nSentiment", (6, 4), "#4338ca"),
        ("Agent 4\nScoring", (8, 4), "#4f46e5"),
        ("Agent 5\nEthics", (10, 4), "#6366f1"),
        ("Agent 6\nPrice Intel", (10, 2), "#7c3aed"),
        ("Agent 7\nPersonalize", (8, 2), "#8b5cf6"),
        ("Agent 8\nAlternatives", (6, 2), "#a855f7"),
        ("Agent 9\nQuery Intel", (4, 2), "#c026d3"),
        ("Agent 10\nFinal", (2, 2), "#db2777"),
    ]

    for label, pos, color in agents:
        draw_agent(ax, label, pos, color)

    draw_arrow(ax, (0.4, 4), (1.6, 4))
    for i in range(4):
        draw_arrow(
            ax,
            (agents[i][1][0] + 0.4, agents[i][1][1]),
            (agents[i + 1][1][0] - 0.4, agents[i + 1][1][1]),
        )

    draw_arrow(ax, (10, 3.8), (10, 2.2))

    for i in range(5, 9):
        draw_arrow(
            ax,
            (agents[i][1][0] - 0.4, agents[i][1][1]),
            (agents[i + 1][1][0] + 0.4, agents[i + 1][1][1]),
        )

    draw_agent(ax, "JSON\nResponse", (0, 2), "#10b981")
    draw_arrow(ax, (1.6, 2), (0.4, 2))

    # External APIs (Agent 2)
    b_api = patches.FancyBboxPatch(
        (3.3, 5.35),
        3.4,
        0.85,
        boxstyle="round,pad=0.08",
        ec="none",
        fc="#f59e0b",
    )
    ax.add_patch(b_api)
    ax.text(
        5.0,
        5.78,
        "DummyJSON  +  DuckDuckGo Instant Answer\n(optional Groq LLM: key features)",
        ha="center",
        va="center",
        color="white",
        fontsize=8,
        fontweight="bold",
    )
    draw_arrow(ax, (4.0, 4.2), (4.0, 5.35))
    draw_arrow(ax, (5.0, 5.35), (5.0, 4.2))

    b_fb = patches.FancyBboxPatch(
        (8.2, 5.35),
        2.2,
        0.55,
        boxstyle="round,pad=0.08",
        ec="none",
        fc="#64748b",
    )
    ax.add_patch(b_fb)
    ax.text(
        9.3,
        5.62,
        "Feedback → JSONL",
        ha="center",
        va="center",
        color="white",
        fontsize=8,
        fontweight="bold",
    )

    plt.title(
        "AuraCart Phase 2 — API-Driven LangGraph Pipeline\n"
        "(Frontend → FastAPI → LangGraph → DummyJSON / DuckDuckGo; LLM optional on Agents 1, 2, 10)",
        fontsize=13,
        fontweight="bold",
        pad=18,
        color="#1e293b",
    )

    plt.tight_layout()
    plt.savefig("architecture_diagram.png", dpi=300, facecolor="#f8fafc", bbox_inches="tight")
    print("Saved architecture_diagram.png")


if __name__ == "__main__":
    create_architecture_diagram()
