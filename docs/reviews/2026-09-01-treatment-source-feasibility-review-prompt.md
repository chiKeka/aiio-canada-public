# Independent review prompt — AI-construction treatment-source feasibility

Review the following AIIO Canada increment as a read-only methods and software
gate. Do not modify files, browse beyond the registered public-source URLs or
infer access to confidential microdata.

## Hash-locked review inputs

| File | SHA-256 |
| --- | --- |
| `data/model/ai_attribution_treatment_source_feasibility_contract_v0.1.json` | `8a1fb433b2a76d1c0582bb6bae811ce1af323532b4a363e3a5dcdf67263e736b` |
| `data/model-runs/ai_attribution_treatment_source_feasibility_v0.1.json` | `c2fdf9152ec9c1acf7a302fb6838851fb1001c530e26815dc5e11a8f5a6f4b26` |
| `research/src/aiio/treatment_source_feasibility.py` | `fd6183e4d8fcbf3745891962190cbeba95da2c16b3e5caef6b85ac33bfb5247c` |
| `research/tests/test_treatment_source_feasibility.py` | `691038d343e89fbd08cf00b2fcdaae7683d77dae2834ccd36c2448923ffdbc16` |
| `data/registry/sources.json` | `f0e98225614a2c9fe4bb99a50b6b8719d5f3090d108c6fdfe7bf666b786a5f8b` |

## Review criteria

1. All seven gates are necessary for the locked quarterly regional causal
   treatment definition, or any proposed change is explicitly justified.
2. Each of the eight candidate assessments is consistent with the source's
   published measure, geography, frequency and public accessibility.
3. The SCIEU instrument is correctly separated from its public aggregate
   release and is not misrepresented as public building-level microdata.
4. Announcements, permit values, broad building investment, NAICS 51 capex,
   operating energy and broad employment cannot authorize realized treatment.
5. Eligibility is an all-gates rule; no composite or inferred allocation is
   silently substituted.
6. The implementation is deterministic, registry-bound and fails closed under
   source, gate, status or publication-boundary drift.
7. Zero eligible sources is not interpreted as zero construction activity, and
   cost/schedule effect fields remain null.

## Required response

Return one JSON object with:

```json
{
  "reviewer": "claude_or_grok",
  "verdict": "pass_or_fail",
  "critical_findings": [],
  "high_findings": [],
  "medium_findings": [],
  "low_findings": [],
  "criterion_results": [
    {"criterion": 1, "status": "pass_or_fail", "reason": "..."}
  ],
  "publication_recommendation": "retain_fail_closed_or_revise"
}
```

A pass is prohibited when any criterion fails or a critical/high finding is
open. This review may approve the feasibility screen; it cannot authorize a
treatment measure or causal effect.
