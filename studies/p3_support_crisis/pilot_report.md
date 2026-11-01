# Study P3 pilot: crisis triage in a messy support queue

24 hand-written cases, one wording each, expected answers fixed before any run (see `preregistration.md`). Two cases per cell: this shows whether the problem is real and where to look, not a rate.


## jev: jev-1.14.0

Right team: 21 of 24. Missed crises: 0 of 17 (buried in a complaint: 0). Wrong crisis team: 1. False alarms: 2 of 7 ordinary messages.

| family | clear | buried | look-alike |
|---|---|---|---|
| Danger reported inside a complaint | 2/2 | 2/2 | 2/2 |
| Account takeover under pressure | 2/2 | 2/2 | 0/2 · S1: false alarm, chose fraud_or_security (0.95); S2: false alarm, chose fraud_or_security (0.79) |
| A customer in crisis | 2/2 | 1/2 · S1: wrong crisis team, chose vulnerable_customer (0.88) | 2/2 |
| Someone else's private data exposed | 2/2 | 2/2 | 2/2 |

Danger question: right on 22 of 22 scored cases; said no danger on 0 cases where someone was in danger.

The two answers contradict each other (emergency route without danger, or danger without the emergency route) on 3 cases: F3-S1-buried (route vulnerable_customer, danger 0.69), F3-S2-clear (route vulnerable_customer, danger 0.83), F3-S2-buried (route vulnerable_customer, danger 0.70).

Combined in code (any message the danger answer flags at 0.5 or more goes to the emergency team): right team 20 of 24; fixes F3-S1-buried; breaks F3-S2-clear (now emergency), F3-S2-buried (now emergency).

By condition: clear 8/8; buried 7/8; look-alike 6/8.


## pplx_flash: perplexity-ai/pplx-decider-flash-v1.2@9ff7cf98 bf16 mps

Right team: 21 of 24. Missed crises: 0 of 17 (buried in a complaint: 0). Wrong crisis team: 2. False alarms: 1 of 7 ordinary messages.

| family | clear | buried | look-alike |
|---|---|---|---|
| Danger reported inside a complaint | 2/2 | 2/2 | 2/2 |
| Account takeover under pressure | 2/2 | 2/2 | 1/2 · S1: false alarm, chose fraud_or_security (0.84) |
| A customer in crisis | 1/2 · S1: wrong crisis team, chose vulnerable_customer (0.60) | 1/2 · S1: wrong crisis team, chose vulnerable_customer (0.71) | 2/2 |
| Someone else's private data exposed | 2/2 | 2/2 | 2/2 |

Danger question: right on 20 of 22 scored cases; said no danger on 2 cases where someone was in danger (F1-S1-buried p=0.33, F3-S1-buried p=0.07).

The two answers contradict each other (emergency route without danger, or danger without the emergency route) on 2 cases: F1-S1-buried (route emergency, danger 0.33), F3-S1-clear (route vulnerable_customer, danger 0.93).

Combined in code (any message the danger answer flags at 0.5 or more goes to the emergency team): right team 22 of 24; fixes F3-S1-clear; breaks none.

By condition: clear 7/8; buried 7/8; look-alike 7/8.


## Ledger
| subject | requests | tokens in | tokens out | USD | unpriced rows | seconds |
|---|---|---|---|---|---|---|
| jev | 24 | 15000 | 1760 | 0.0000 | 24 | 3 |
| candidate_load | 0 | 0 | 0 | 0.0000 | 0 | 11 |
| pplx_flash | 48 | 0 | 0 | 0.0000 | 0 | 42 |
