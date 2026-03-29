"""
Visa type definitions and per-visa context strings.

These context strings are injected into every LLM prompt to ensure answers
are specific to the user's visa type. The context highlights the key
constraints and rights for each visa, so the model focuses on what matters.
"""

from enum import Enum


class VisaType(str, Enum):
    """
    UK visa types supported in the UKReady MVP.

    Uses string enum so values are serialisable as JSON and comparable
    to plain strings (important for FastAPI request parsing).
    """

    GRADUATE = "GRADUATE"
    SKILLED_WORKER = "SKILLED_WORKER"
    STUDENT = "STUDENT"
    ILR = "ILR"


# Per-visa system context injected into every prompt.
# Written to be accurate, concise, and actionable for the LLM.
VISA_CONTEXT: dict[VisaType, str] = {
    VisaType.GRADUATE: (
        "The user is on a GRADUATE VISA (also called the Graduate Route). "
        "Key facts:\n"
        "- Duration: 2 years (3 years if they hold a PhD from a UK university).\n"
        "- Work rights: Can work in any job, at any salary, for any employer — "
        "no sponsorship required. Can be self-employed or work as a contractor.\n"
        "- Restrictions: Cannot access public funds. Cannot extend this visa. "
        "After it expires, must switch to another visa (e.g. Skilled Worker) to stay.\n"
        "- Switching: Can switch to Skilled Worker, Global Talent, or other routes "
        "from inside the UK before the visa expires.\n"
        "- Note: The Graduate visa does not lead directly to ILR — continuous "
        "residence in the UK for 5 years on qualifying visas (e.g. Skilled Worker) "
        "is needed for ILR."
    ),
    VisaType.SKILLED_WORKER: (
        "The user is on a SKILLED WORKER VISA. "
        "Key facts:\n"
        "- Tied to a specific employer (sponsor) and a specific job (SOC code). "
        "Cannot change employers without applying for a new visa or updating the CoS.\n"
        "- Salary: Must meet the general threshold (£38,700 from April 2024) OR "
        "the going rate for the specific SOC code, whichever is higher. "
        "Shortage occupation discounts no longer apply after April 2024.\n"
        "- Working additional jobs: Can take supplementary employment (up to 20 hrs/week) "
        "in the same or lower SOC code, or in shortage occupations.\n"
        "- ILR path: After 5 continuous years on qualifying visas (including Skilled Worker), "
        "can apply for Indefinite Leave to Remain.\n"
        "- Self-employment: Cannot be self-employed (outside of supplementary employment rules)."
    ),
    VisaType.STUDENT: (
        "The user is on a STUDENT VISA. "
        "Key facts:\n"
        "- Work limit during term-time: Maximum 20 hours per week. "
        "Working more than 20 hours per week during term-time is a visa breach.\n"
        "- During official holidays: Can work full-time (no hour limit).\n"
        "- Job type: Cannot work as a professional sportsperson, entertainer, or in "
        "most self-employed roles.\n"
        "- After graduation: Can switch to Graduate visa to stay and work after completing "
        "a qualifying UK degree.\n"
        "- Work restrictions apply specifically during the course — check the CAS "
        "(Confirmation of Acceptance for Studies) for any additional restrictions."
    ),
    VisaType.ILR: (
        "The user has INDEFINITE LEAVE TO REMAIN (ILR). "
        "Key facts:\n"
        "- No work restrictions: Can work in any job, for any employer, "
        "at any salary, full-time or part-time, self-employed or employed.\n"
        "- No visa expiry: ILR does not expire, but the biometric residence permit (BRP) "
        "does. The ILR status itself is permanent (unless it lapses after 2+ years abroad).\n"
        "- Public funds: Entitled to access public funds (benefits, NHS, etc.).\n"
        "- Path to citizenship: Can apply for British citizenship after 12 months of "
        "holding ILR (if meeting other requirements like Life in the UK test).\n"
        "- Lapse risk: ILR lapses if absent from the UK for more than 2 consecutive years."
    ),
}


def get_visa_display_name(visa_type: VisaType) -> str:
    """Return a human-readable display name for a visa type."""
    names = {
        VisaType.GRADUATE: "Graduate Visa",
        VisaType.SKILLED_WORKER: "Skilled Worker Visa",
        VisaType.STUDENT: "Student Visa",
        VisaType.ILR: "Indefinite Leave to Remain (ILR)",
    }
    return names[visa_type]
