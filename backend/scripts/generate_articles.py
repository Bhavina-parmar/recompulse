import random
import time
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "recompulse.db"

CATEGORIES = {
    "Tech": [
        "Artificial Intelligence",
        "Machine Learning",
        "Cloud Computing",
        "Cybersecurity",
        "Blockchain",
        "Quantum Computing"
    ],
    "Business": [
        "Startup Ecosystems",
        "Venture Capital",
        "Global Markets",
        "Digital Transformation",
        "Leadership Strategy"
    ],
    "Health": [
        "Mental Wellness",
        "Nutrition Science",
        "Fitness Innovation",
        "Medical Research",
        "Public Health Policy"
    ],
    "Sports": [
        "Football Analytics",
        "Olympic Performance",
        "Sports Technology",
        "Athlete Psychology",
        "Team Strategy Evolution"
    ],
    "Lifestyle": [
        "Productivity Habits",
        "Remote Work Trends",
        "Sustainable Living",
        "Personal Development",
        "Travel Culture"
    ]
}


def generate_paragraph(topic):
    return (
        f"{topic} is rapidly evolving in today's world. "
        f"Experts believe that advancements in {topic.lower()} are reshaping industries and influencing global trends. "
        f"Organizations are investing heavily in innovation, research, and infrastructure to stay competitive. "
        f"The long-term implications of {topic.lower()} will likely redefine how individuals and businesses operate.\n\n"
        f"Recent studies indicate that adoption rates are increasing significantly. "
        f"As technology and policy frameworks mature, the ecosystem surrounding {topic.lower()} continues to expand. "
        f"Stakeholders must adapt quickly to leverage emerging opportunities and mitigate potential risks.\n\n"
        f"Looking ahead, the integration of data-driven decision making and automation will accelerate progress. "
        f"Strategic planning, ethical considerations, and sustainable practices will determine the trajectory of {topic.lower()} in the coming decade."
    )


def generate_articles(total_articles=60):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM items")

    article_id = 1
    now = int(time.time())

    for category, topics in CATEGORIES.items():
        for topic in topics:
            for _ in range(2):  # two variations per topic
                title = f"{topic} Trends and Future Outlook"
                content = generate_paragraph(topic)

                created_at = now - random.randint(0, 60 * 60 * 24 * 30)

                cursor.execute(
                    """
                    INSERT INTO items (id, title, category, content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (article_id, title, category, content, created_at)
                )

                article_id += 1

    conn.commit()
    conn.close()

    print(f"✅ Inserted {article_id - 1} realistic articles.")


if __name__ == "__main__":
    generate_articles()