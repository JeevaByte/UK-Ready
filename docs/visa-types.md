# UK Visa Types — UKReady Reference

This document explains the four visa types supported in the UKReady MVP. It is used by contributors to understand the constraints each visa type carries, so they can verify that AI responses are accurate.

> **Important:** Visa rules change frequently. Always verify current rules at [gov.uk](https://www.gov.uk) and consult a registered immigration solicitor for personal advice.

---

## Graduate Visa

**Enum value:** `GRADUATE`

**Official gov.uk page:** https://www.gov.uk/graduate-visa

### Overview
The Graduate visa (also called the Graduate Route) allows international students who have completed a qualifying UK degree to stay and work in the UK after graduation. It was introduced in July 2021.

### Key facts

| Rule | Detail |
|------|--------|
| Duration | 2 years (3 years if you hold a PhD from a UK university) |
| Work rights | Any job, any employer, any salary — no sponsorship required |
| Self-employment | Allowed |
| Multiple employers | Allowed (e.g. two part-time jobs) |
| Switching from | Student visa (must apply before Student visa expires) |
| Switching to | Skilled Worker, Global Talent, or other eligible routes |
| Public funds | Not allowed |
| ILR path | Not directly — need to switch to Skilled Worker (etc.) and complete 5 years |
| Extending | Cannot extend the Graduate visa |

### Common Q&A this visa generates
- Can I change employer? **Yes, freely**
- Can I work part-time? **Yes**
- Can I freelance/contract? **Yes**
- Can I work in any industry? **Yes, almost all (some regulated professions have their own requirements)**
- What happens when it expires? **Must leave or switch to another visa before expiry**

---

## Skilled Worker Visa

**Enum value:** `SKILLED_WORKER`

**Official gov.uk page:** https://www.gov.uk/skilled-worker-visa

### Overview
The Skilled Worker visa replaced Tier 2 (General) in December 2020. It is the main route for non-UK nationals to work in a skilled job in the UK. It requires sponsorship from an employer with a Home Office sponsor licence.

### Key facts

| Rule | Detail |
|------|--------|
| Sponsor required | Yes — employer must hold a valid sponsor licence |
| Job code | Tied to a specific SOC code on the Certificate of Sponsorship (CoS) |
| Salary threshold | £38,700/year (from April 2024) OR the going rate for the SOC code, whichever is higher |
| Change employer | Requires a new visa application or CoS update |
| Change job (same sponsor) | Requires updated CoS if significant change in duties or pay |
| Supplementary employment | Up to 20 hrs/week in the same or lower SOC code, or shortage occupations |
| Self-employment | Not permitted (except via supplementary employment rules) |
| Public funds | Not allowed |
| ILR path | After 5 continuous years on qualifying visas (including Skilled Worker) |
| Duration | Up to 5 years per grant; can extend |

### Salary threshold detail (April 2024 onwards)
- General threshold: £38,700/year
- New entrant rate (for those under 26, recent graduates, etc.): £30,960
- National Living Wage jobs: must still meet sector going rates
- Shortage Occupation List discounts: **removed** from April 2024

### Common Q&A this visa generates
- Can I change employer? **No — must get new CoS and apply for visa update**
- Can I get a second job? **Yes, up to 20 hrs/week under supplementary employment rules**
- What is my minimum salary? **£38,700 or going rate — whichever is higher**
- Can I freelance? **No**
- Can I take a pay cut below the threshold? **No — this breaches visa conditions**

---

## Student Visa

**Enum value:** `STUDENT`

**Official gov.uk page:** https://www.gov.uk/student-visa

### Overview
The Student visa (formerly Tier 4) allows non-UK nationals to study at a UK Higher Education Institution (HEI). It has strict work hour limits during term time.

### Key facts

| Rule | Detail |
|------|--------|
| Work hours (term-time) | Maximum 20 hours per week |
| Work hours (holidays) | Full-time (no limit) during official university vacation periods |
| Work type | Most jobs allowed; cannot be a professional sportsperson or entertainer |
| Self-employment | Not permitted |
| Multiple employers | Allowed, but total hours across all jobs ≤ 20/week in term time |
| After graduation | Can switch to Graduate visa (if studying at an eligible HEI) |
| Public funds | Not allowed |

### What counts as "term time"?
Term time is defined by your university's academic calendar, not by when you personally have classes. Check your university's official term dates.

### Common Q&A this visa generates
- How many hours can I work? **20 hrs/week during term; full-time in official holidays**
- Can I work on placement? **Yes, if it's part of the course (counted toward course hours)**
- Can I freelance? **No**
- Can I stay after graduation? **Yes — apply for Graduate visa before Student visa expires**

---

## Indefinite Leave to Remain (ILR)

**Enum value:** `ILR`

**Official gov.uk page:** https://www.gov.uk/indefinite-leave-to-remain

### Overview
Indefinite Leave to Remain (ILR) is a form of permanent residence in the UK. It has no expiry on the status itself (though the BRP document expires). Holders have full work rights and access to public funds.

### Key facts

| Rule | Detail |
|------|--------|
| Work restrictions | None — any job, any salary, any employer |
| Self-employment | Allowed |
| Public funds | Entitled to full access |
| ILR expiry | The status doesn't expire, but the BRP card does (renew the card, not the status) |
| Lapse rule | ILR lapses if absent from UK for 2+ consecutive years |
| Citizenship path | Can apply for British citizenship after 12 months of ILR + other requirements |
| Life in the UK test | Must have passed it (usually required as part of ILR application) |

### Common Q&A this visa generates
- Can I work in any job? **Yes, no restrictions**
- Can I start a business? **Yes**
- Does ILR expire? **The status doesn't, but the biometric card does (renew it)**
- When can I apply for citizenship? **After 12 months of ILR + other eligibility criteria**
- What if I move abroad? **ILR lapses after 2 consecutive years outside the UK**

---

## Visa Types in Code

The visa type is represented as a Python enum in `backend/app/models/visa.py`:

```python
class VisaType(str, Enum):
    GRADUATE = "GRADUATE"
    SKILLED_WORKER = "SKILLED_WORKER"
    STUDENT = "STUDENT"
    ILR = "ILR"
```

And injected into every LLM prompt via the `VISA_CONTEXT` dict in the same file. If you believe a visa context description is inaccurate, please open a GitHub issue with the correct gov.uk citation.

---

## Planned Additions (Future Phases)

| Visa | Status |
|------|--------|
| Global Talent visa | Planned (Month 3+) |
| BN(O) Overseas National visa | Planned |
| Innovator Founder visa | Planned |
| Family visa | Considering |
| UK Ancestry visa | Considering |
