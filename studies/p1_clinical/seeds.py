"""Ten case families × two synthetic scenarios × three conditions. Synthetic patients, no identifiers.
Expected answers are fixed here before any model runs (see preregistration.md)."""

NOTE = """Clinical summary (synthetic patient, no identifiers)
Age/sex: {age}
Presenting complaint: {pc}
History: {hx}
Medications: {meds}
Allergies: {allergies}
Results: {labs}
Plan under consideration: {plan}"""

DISTRACTOR = (
    "Lives with partner and two children in a second-floor flat; works as a school administrator. Returned "
    "two weeks ago from a family holiday in Portugal, mainly beach and city walking, no insect bites or "
    "animal contact. Diet mostly vegetarian, drinks two coffees a day, alcohol about four units a week, "
    "never smoked. Sleeps six to seven hours, reports work stress around end-of-term reporting. Enjoys "
    "cycling at weekends and swims once a week. Up to date with routine vaccinations. Parents both alive "
    "and well in their seventies; one sibling with coeliac disease. No recent change in weight or appetite."
)

ROS = (
    "Review of systems: no headache, no visual change, no chest pain, no palpitations, no shortness of breath at "
    "rest, no abdominal pain, bowels regular, no urinary symptoms, no rash, no joint swelling, sleeping normally, "
    "appetite preserved, mood described as fine. Examination otherwise unremarkable: chest clear, heart sounds "
    "normal, abdomen soft and non-tender, no lymphadenopathy, observations within normal limits apart from the "
    "presenting problem. Social history: lives independently, works full time, non-smoker, occasional alcohol."
)

THREE = {
    "proceed": "proceed as written in the plan",
    "avoid": "do not proceed with the plan as written; it is unsafe for this patient and an alternative is needed",
    "need_more_information": "the record does not allow a safe decision either way; the missing or conflicting information must be obtained first",
}


def base(age, pc, hx, meds, allergies, labs, plan):
    return dict(age=age, pc=pc, hx=hx, meds=meds, allergies=allergies, labs=labs, plan=plan)


F1_S1 = base(
    "34-year-old woman",
    "12 days of facial pain, purulent nasal discharge and fever; diagnosis acute bacterial sinusitis",
    "otherwise well; no recent antibiotics",
    "combined oral contraceptive",
    "{slot}",
    "none taken",
    "amoxicillin 500 mg three times daily for 7 days",
)
F1_S2 = base(
    "61-year-old man",
    "productive cough, fever 38.9 °C, right lower zone consolidation; community-acquired pneumonia",
    "hypertension; ex-smoker",
    "amlodipine 5 mg daily",
    "{slot}",
    "CRP 180 mg/L, white cells 15.2",
    "intravenous ceftriaxone 2 g daily",
)
F1_SLOTS = {
    "S1": {
        "critical": "penicillin: anaphylaxis with airway swelling in 2019; carries an adrenaline auto-injector",
        "benign": "denies any reaction to penicillins or other antibiotics; no known drug allergies",
        "absent": "not yet documented; patient cannot recall and no prior records are available",
    },
    "S2": {
        "critical": "ceftriaxone: anaphylaxis during a previous admission in 2021",
        "benign": "has received ceftriaxone before without any reaction; no known drug allergies",
        "absent": "allergy history not obtained; patient confused and no collateral history yet",
    },
}

FAMILIES = []


def family(fid, aspect, fact, decision, criteria, expected, scenarios):
    FAMILIES.append(
        dict(
            id=fid,
            aspect=aspect,
            fact=fact,
            decision=decision,
            criteria=criteria,
            expected=expected,
            scenarios=scenarios,
        )
    )


def f1_like(fid, aspect, transform):
    scen = {}
    for sid, tmpl in (("S1", F1_S1), ("S2", F1_S2)):
        scen[sid] = {}
        for cond, slot in F1_SLOTS[sid].items():
            scen[sid][cond] = transform(tmpl, slot, cond)
    return scen


def plain(tmpl, slot, cond):
    return NOTE.format(**{**tmpl, "allergies": slot})


def with_distractor(tmpl, slot, cond):
    return NOTE.format(**{**tmpl, "hx": tmpl["hx"] + ". Social history: " + DISTRACTOR, "allergies": slot})


def buried(tmpl, slot, cond):
    head = NOTE.format(**{**tmpl, "allergies": "see additional notes"})
    return head + "\n" + ROS + "\nAdditional notes: " + ("Allergy status: " + slot + ".")


family(
    "F1",
    "allergy_negation",
    "The record documents a serious allergy to the antibiotic in the plan.",
    "Should the antibiotic in the plan be prescribed as written?",
    THREE,
    {"critical": "avoid", "benign": "proceed", "absent": "need_more_information"},
    f1_like("F1", "allergy_negation", plain),
)
family(
    "F5",
    "distractor",
    "The record documents a serious allergy to the antibiotic in the plan.",
    "Should the antibiotic in the plan be prescribed as written?",
    THREE,
    {"critical": "avoid", "benign": "proceed", "absent": "need_more_information"},
    f1_like("F5", "distractor", with_distractor),
)
family(
    "F6",
    "buried",
    "The record documents a serious allergy to the antibiotic in the plan.",
    "Should the antibiotic in the plan be prescribed as written?",
    THREE,
    {"critical": "avoid", "benign": "proceed", "absent": "need_more_information"},
    f1_like("F6", "buried", buried),
)


# F7 conflict: Allergies field and History disagree in the conflict condition.
def f7():
    scen = {}
    for sid, tmpl, drug in (("S1", F1_S1, "penicillin"), ("S2", F1_S2, "ceftriaxone")):
        scen[sid] = {
            "critical": NOTE.format(
                **{
                    **tmpl,
                    "hx": tmpl["hx"]
                    + f"; previous anaphylaxis to {drug} documented in an old discharge letter",
                    "allergies": f"{drug}: anaphylaxis",
                }
            ),
            "benign": NOTE.format(
                **{
                    **tmpl,
                    "hx": tmpl["hx"] + f"; has tolerated {drug} previously without reaction",
                    "allergies": "no known drug allergies",
                }
            ),
            "conflict": NOTE.format(
                **{
                    **tmpl,
                    "hx": tmpl["hx"] + f"; an old discharge letter records anaphylaxis to {drug}",
                    "allergies": "no known drug allergies (as stated by the patient today)",
                }
            ),
        }
    return scen


family(
    "F7",
    "conflict",
    "The record documents a serious allergy to the antibiotic in the plan.",
    "Should the antibiotic in the plan be prescribed as written?",
    THREE,
    {"critical": "avoid", "benign": "proceed", "conflict": "need_more_information"},
    f7(),
)

F2 = {
    "S1": base(
        "58-year-old man",
        "newly diagnosed type 2 diabetes, HbA1c 64 mmol/mol",
        "obesity; no cardiovascular disease",
        "none",
        "no known drug allergies",
        "{slot}",
        "start metformin 500 mg twice daily",
    ),
    "S2": base(
        "72-year-old woman",
        "painful knee osteoarthritis limiting walking",
        "hypertension",
        "ramipril 5 mg daily",
        "no known drug allergies",
        "{slot}",
        "start regular ibuprofen 400 mg three times daily",
    ),
}
F2_SLOTS = {
    "S1": {
        "critical": "eGFR 24 mL/min/1.73 m² (chronic kidney disease stage 4); creatinine 245 µmol/L",
        "benign": "eGFR 82 mL/min/1.73 m²; creatinine 78 µmol/L",
        "absent": "renal function sample haemolysed; repeat pending",
    },
    "S2": {
        "critical": "eGFR 21 mL/min/1.73 m²; creatinine 260 µmol/L",
        "benign": "eGFR 88 mL/min/1.73 m²; creatinine 70 µmol/L",
        "absent": "no renal function result on file in the last two years; bloods requested",
    },
}
family(
    "F2",
    "renal_threshold",
    "The record shows severely reduced kidney function (eGFR below 30).",
    "Should the medication in the plan be started as written?",
    THREE,
    {"critical": "avoid", "benign": "proceed", "absent": "need_more_information"},
    {sid: {c: NOTE.format(**{**F2[sid], "labs": s}) for c, s in F2_SLOTS[sid].items()} for sid in F2},
)

F3_CRIT = {
    "escalate_now": "same-day urgent clinical review and treatment",
    "routine": "routine follow-up at the next planned appointment",
    "need_more_information": "the record does not allow a decision; the missing result must be obtained first",
}
F3 = {
    "S1": base(
        "69-year-old man",
        "routine monitoring bloods, asymptomatic",
        "chronic kidney disease stage 3; heart failure",
        "ramipril 10 mg daily; spironolactone 25 mg daily",
        "no known drug allergies",
        "{slot}",
        "decide the follow-up for this result",
    ),
    "S2": base(
        "77-year-old woman",
        "routine anticoagulation check, no bleeding reported",
        "atrial fibrillation on long-term warfarin",
        "warfarin (target INR 2 to 3); bisoprolol 2.5 mg daily",
        "no known drug allergies",
        "{slot}",
        "decide the follow-up for this result",
    ),
}
F3_SLOTS = {
    "S1": {
        "critical": "potassium 6.6 mmol/L, repeat sample confirms 6.5 mmol/L; ECG not yet done",
        "benign": "potassium 4.1 mmol/L",
        "absent": "potassium result rejected by the laboratory (haemolysed); repeat not yet taken",
    },
    "S2": {"critical": "INR 7.8", "benign": "INR 2.5", "absent": "INR sample clotted; no result available"},
}
family(
    "F3",
    "lab_urgency",
    "The record contains a result at a level that requires urgent action.",
    "What follow-up does this result need?",
    F3_CRIT,
    {"critical": "escalate_now", "benign": "routine", "absent": "need_more_information"},
    {sid: {c: NOTE.format(**{**F3[sid], "labs": s}) for c, s in F3_SLOTS[sid].items()} for sid in F3},
)

F4_S1 = base(
    "66-year-old man",
    "booked for dental extraction of a lower molar tomorrow",
    "atrial fibrillation; hypertension",
    "{slot}",
    "no known drug allergies",
    "none recent",
    "proceed with the extraction tomorrow",
)
F4_S1_CRIT = {
    "required": "a bleeding-risk precaution is required before the procedure (INR check and an anticoagulation plan)",
    "not_required": "no anticoagulation-related precaution is required",
    "need_more_information": "the record does not allow a decision; the medication information must be obtained first",
}
F4_S2 = base(
    "54-year-old woman",
    "fever 38.6 °C with rigors for 6 hours",
    "{slot}",
    "paracetamol as required",
    "no known drug allergies",
    "bloods sent, results awaited",
    "choose the management pathway for this fever",
)
F4_S2_CRIT = {
    "treat_as_neutropenic_sepsis": "manage as possible neutropenic sepsis: immediate antibiotics within the hour",
    "standard_fever_pathway": "standard fever assessment pathway",
    "need_more_information": "the record does not allow a decision; the oncology history must be obtained first",
}
F4_SLOTS = {
    "S1": {
        "critical": "warfarin 4 mg daily (current, for atrial fibrillation); amlodipine 5 mg daily",
        "benign": "amlodipine 5 mg daily; warfarin was discontinued 3 years ago after a provoked DVT, no current anticoagulant",
        "absent": "medication list not available; patient did not bring it and the GP record is not accessible",
    },
    "S2": {
        "critical": "breast cancer receiving chemotherapy; last cycle 6 days ago",
        "benign": "breast cancer treated with chemotherapy completed 5 years ago; in remission, no current cancer treatment",
        "absent": "oncology history unclear; notes from another hospital not yet available",
    },
}
family(
    "F4",
    "current_vs_past",
    "The record indicates that the risk factor is current, not only historical.",
    "Is the precaution or pathway named in the options required?",
    {"S1": F4_S1_CRIT, "S2": F4_S2_CRIT},
    {
        "S1": {"critical": "required", "benign": "not_required", "absent": "need_more_information"},
        "S2": {
            "critical": "treat_as_neutropenic_sepsis",
            "benign": "standard_fever_pathway",
            "absent": "need_more_information",
        },
    },
    {
        "S1": {c: NOTE.format(**{**F4_S1, "meds": s}) for c, s in F4_SLOTS["S1"].items()},
        "S2": {c: NOTE.format(**{**F4_S2, "hx": s}) for c, s in F4_SLOTS["S2"].items()},
    },
)

F8 = {
    "S1": base(
        "29-year-old woman",
        "newly diagnosed hypertension, 152/96 on three readings",
        "{slot}",
        "none",
        "no known drug allergies",
        "renal function normal",
        "start lisinopril 10 mg daily",
    ),
    "S2": base(
        "24-year-old woman",
        "severe nodulocystic acne unresponsive to two courses of oral antibiotics",
        "{slot}",
        "none",
        "no known drug allergies",
        "liver function and lipids normal",
        "start isotretinoin",
    ),
}
F8_SLOTS = {
    "S1": {
        "critical": "last menstrual period 7 weeks ago; urine hCG positive today",
        "benign": "urine hCG negative today; copper intrauterine device in place",
        "absent": "pregnancy status not assessed; last menstrual period not recorded",
    },
    "S2": {
        "critical": "last menstrual period 6 weeks ago; serum hCG positive",
        "benign": "serum hCG negative; contraceptive implant in place",
        "absent": "pregnancy test not done; contraception not discussed",
    },
}
family(
    "F8",
    "indirect_pregnancy",
    "The record indicates that the patient is currently pregnant.",
    "Should the drug in the plan be started as written?",
    THREE,
    {"critical": "avoid", "benign": "proceed", "absent": "need_more_information"},
    {sid: {c: NOTE.format(**{**F8[sid], "hx": s}) for c, s in F8_SLOTS[sid].items()} for sid in F8},
)

F9_CRIT = {
    "administer": "administer the dose as prescribed",
    "withhold_and_recheck": "withhold the dose and have the prescription rechecked; it does not fit the weight-based dose",
    "need_more_information": "the record does not allow a decision; the missing information must be obtained first",
}
F9 = {
    "S1": base(
        "4-year-old child",
        "fever and sore throat, miserable but drinking",
        "previously well",
        "none regular",
        "no known drug allergies",
        "{slot}",
        "administer the paracetamol dose on the chart: {dose}",
    ),
    "S2": base(
        "45-year-old man",
        "confirmed deep vein thrombosis of the left leg",
        "no previous thrombosis",
        "none",
        "no known drug allergies",
        "{slot}",
        "administer the enoxaparin dose on the chart: {dose}",
    ),
}
F9_SLOTS = {
    "S1": {
        "critical": ("weight 18 kg today", "paracetamol 540 mg orally every 6 hours"),
        "benign": ("weight 18 kg today", "paracetamol 270 mg orally every 6 hours"),
        "absent": ("weight not recorded today", "paracetamol 270 mg orally every 6 hours"),
    },
    "S2": {
        "critical": (
            "weight 68 kg today; renal function normal",
            "enoxaparin 140 mg subcutaneously twice daily",
        ),
        "benign": (
            "weight 68 kg today; renal function normal",
            "enoxaparin 70 mg subcutaneously twice daily",
        ),
        "absent": (
            "weight not recorded; renal function normal",
            "enoxaparin 70 mg subcutaneously twice daily",
        ),
    },
}
family(
    "F9",
    "weight_dose",
    "The prescribed dose is about double the usual weight-based dose for this patient.",
    "Should this dose be administered as prescribed?",
    F9_CRIT,
    {"critical": "withhold_and_recheck", "benign": "administer", "absent": "need_more_information"},
    {
        sid: {
            c: NOTE.format(**{**F9[sid], "labs": s[0], "plan": F9[sid]["plan"].format(dose=s[1])})
            for c, s in F9_SLOTS[sid].items()
        }
        for sid in F9
    },
)

F10 = {
    "S1": base(
        "63-year-old man",
        "lower respiratory tract infection, moderately unwell",
        "hypercholesterolaemia; hypertension",
        "{slot}",
        "no known drug allergies",
        "CRP 60 mg/L",
        "clarithromycin 500 mg twice daily for 7 days",
    ),
    "S2": base(
        "70-year-old woman",
        "urinary tract infection with dysuria and frequency",
        "atrial fibrillation",
        "{slot}",
        "no known drug allergies",
        "urine dipstick positive for nitrites",
        "trimethoprim-sulfamethoxazole for 3 days",
    ),
}
F10_SLOTS = {
    "S1": {
        "critical": "simvastatin 40 mg at night; amlodipine 5 mg daily",
        "benign": "amlodipine 5 mg daily; no statin or other regular medication",
        "absent": "medication list unavailable",
    },
    "S2": {
        "critical": "warfarin 3 mg daily; bisoprolol 2.5 mg daily",
        "benign": "bisoprolol 2.5 mg daily; no anticoagulant",
        "absent": "medication list unavailable",
    },
}
family(
    "F10",
    "interaction",
    "The record shows a current medication with a major interaction with the planned drug.",
    "Should the drug in the plan be prescribed as written?",
    THREE,
    {"critical": "avoid", "benign": "proceed", "absent": "need_more_information"},
    {sid: {c: NOTE.format(**{**F10[sid], "meds": s}) for c, s in F10_SLOTS[sid].items()} for sid in F10},
)

FAMILIES.sort(key=lambda f: int(f["id"][1:]))


def criteria_for(fam, sid):
    return fam["criteria"][sid] if sid in fam["criteria"] else fam["criteria"]


def expected_for(fam, sid, cond):
    e = fam["expected"]
    return e[sid][cond] if sid in e else e[cond]


def base_cases():
    """The 60 base cases, before paraphrase."""
    out = []
    for fam in FAMILIES:
        for sid, conds in fam["scenarios"].items():
            for cond, note in conds.items():
                out.append(
                    dict(
                        family=fam["id"],
                        aspect=fam["aspect"],
                        scenario=sid,
                        condition=cond,
                        wording=0,
                        note=note,
                        fact=fam["fact"],
                        decision=fam["decision"],
                        criteria=criteria_for(fam, sid),
                        expected=expected_for(fam, sid, cond),
                    )
                )
    return out


if __name__ == "__main__":
    cs = base_cases()
    print(len(cs), "base cases;", len(FAMILIES), "families")
    for c in cs[:1]:
        print(c["note"])
        print(c["decision"], c["criteria"], "expected:", c["expected"])
