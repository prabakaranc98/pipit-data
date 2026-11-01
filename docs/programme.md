# Programme P: five studies on one model

## In plain words

We take one small decision model, Perplexity's 4B decider, and ask it the same kind of question in five areas of
life: a clinic, a legal office, a support desk, a study of people, and a money decision. In each area we pick one
narrow thing that is easy to get wrong and matters when it is wrong. We build cases where we know the right answer
in advance, because we planted the fact that decides it. Then we count how often the model gets it wrong, say how
sure we are given how few cases we ran, and say what it cost. When the evidence is strong enough, that is a finding,
and the finding becomes the start of a deeper study. When it is not, the lab models suggest where to look next,
and a person decides.

The point of doing five is not five reports. It is to learn what this model can and cannot do, which helper models
were worth their cost, and whether the method itself holds up outside the clinic.

## The five studies, each with an example

| Study | Where | The one thing we test | An example case |
| --- | --- | --- | --- |
| P1 clinical | a ward or a GP surgery | can the model read a record and keep a patient safe | a child weighs 18 kg and the chart says 540 mg of paracetamol: give it, hold it, or ask? |
| P2 legal | a compliance desk | does it apply an exception and count a deadline correctly | a notice must be sent within 30 business days of delivery; delivery was a Friday; is Tuesday week five too late? |
| P3 customer support | a help desk | does it follow a written policy with time windows and tiers | returns are accepted 30 days from delivery, not from order; the order was 35 days ago, delivery 28: eligible? |
| P4 behavioural science | a study of people | is its judgment steady when the same fact is worded two ways | "9 in 10 recover" and "1 in 10 do not" describe the same outcome: does the answer change? |
| P5 economics | a money decision | does it compare amounts when units and periods differ | a fee of 1.2 percent a month against 12 percent a year: which is cheaper? |

Each study has three kinds of case for every example: the fact is there and should change the decision; the fact
is there and is harmless; the fact is missing or the record contradicts itself, so the right answer is "ask".

## How every study works, step by step

1. **Write the question first.** What could go wrong, split into four kinds: the model misreads, the model reads
   but cannot compute or compare, the model cannot infer from indirect clues, the model commits when it should ask.
2. **Build the cases with the answer planted.** Two scenarios per family, the three kinds of case, two wordings
   of each. A helper model rewrites the wording; a different helper model checks the fact is still there. Code
   checks for broken or cut-off text. Anything with a number is checked by code, not by a model.
3. **Run the models.** The model under test only answers. A second model answers too, for comparison, never as a
   teacher. Every call is saved and priced.
4. **Count and say how sure we are.** For every family and kind of case: how many wrong, and the range the true
   rate could be in given how few cases we ran. Wrong answers are sorted by how bad they are: unsafe, too cautious,
   or sure when it should have asked.
5. **A person reads the flags.** Where the helper model disagreed with the planted answer, a person decides who
   was right, and both readings are reported.
6. **Decide.** Strong evidence becomes a finding and opens a deeper study on fresh cases the model has never seen.
   Weak evidence sends the helper models to propose sharper questions and new cases; a person keeps or drops them.
7. **Keep the record.** Every study writes the same report, as text and as data, so the five can be read side by
   side: what was found, how sure, what it cost, which helper models were used.

## What the programme must answer at the end

1. About the model: what it can do, where it breaks, and what is still unknown, in words a clinician or a support
   lead would understand.
2. About the helper models: which ones were right often enough to be worth their cost, in which job.
3. About the method: how many cases a finding took compared with just sampling evenly, and where the method beat
   the published references in practice and where it did not.

## Order of work

First the instrument proof (M1) and the clinical dose follow-up, because they cost nothing in helper-model calls
and tell us whether the counting rules can be trusted. Then the shared protocol and the common report format. Then
the four new studies. Then the programme report and the viewer.
