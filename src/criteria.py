"""Six criteria for low/medium/high assessment (used in prompts and output)."""

# Keys used in JSON and score rows
CRITERIA_6 = [
    "fiscal_impact",
    "equity_access",
    "political_feasibility",
    "sustainability",
    "team_retention",
    "accountability",
]

# Display labels for table headers
CRITERIA_LABELS = {
    "fiscal_impact": "Fiscal Impact",
    "equity_access": "Equity & Access",
    "political_feasibility": "Political Feasibility",
    "sustainability": "Sustainability",
    "team_retention": "Team Retention",
    "accountability": "Accountability",
}

# Sub-criteria for prompts
CRITERIA_SUB = {
    "fiscal_impact": "Revenue, debt, public cost",
    "equity_access": "Community benefit, affordability",
    "political_feasibility": "Legal, legislative, stakeholder",
    "sustainability": "Long-term adaptability, risk",
    "team_retention": "Major league / franchise retention likelihood",
    "accountability": "Oversight, enforceability",
}

VALID_LEVELS = ("LOW", "MEDIUM", "HIGH")

# For averaging: LOW=1, MEDIUM=2, HIGH=3
LEVEL_TO_NUM = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
NUM_TO_LEVEL = {1: "LOW", 2: "MEDIUM", 3: "HIGH"}
