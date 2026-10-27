# Data handling & ethics notes

- **No real patient data is used anywhere in this repository.** All
  audio samples, transcripts, and clinical notes are synthetically
  generated (see `ml/data/generate_synthetic_notes.py`) or templated
  from public, de-identified example formats.
- CareScribe is not (yet) a certified medical device. It has not undergone clinical validation, has no regulatory
  clearance (e.g. MDR/CE marking), and must not be connected to real
  patient-identifiable data or used to inform real clinical decisions.
- The **Validator Agent** and human-review gate exist specifically to
  model the principle that a clinician, not the model, makes the final
  call — any real-world descendant of this project should keep that
  invariant.
- Before CareScribe is deployed against real clinical data, it will
  need, at minimum, a DPIA, a legal basis under GDPR Art. 9(2)(h) /
  national health-data law, a BAA-equivalent data processing agreement
  with any infrastructure provider, de-identification/pseudonymization
  before any non-clinical environment, and an audit log of every access
  to patient data. These are tracked as prerequisites for any production
  rollout (see [`ROADMAP.md`](ROADMAP.md)).
