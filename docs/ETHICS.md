# Data handling & ethics notes

- **No real patient data is used anywhere in this repository.** All
  audio samples, transcripts, and clinical notes are synthetically
  generated (see `ml/data/generate_synthetic_notes.py`) or templated
  from public, de-identified example formats.
- The system is a technology demonstration, not a certified medical
  device. It has not undergone clinical validation, has no regulatory
  clearance (e.g. MDR/CE marking), and must not be connected to real
  patient-identifiable data or used to inform real clinical decisions.
- The **Validator Agent** and human-review gate exist specifically to
  model the principle that a clinician, not the model, makes the final
  call — any real-world descendant of this project should keep that
  invariant.
- If adapting this project to work with real clinical data: you would
  need, at minimum, a DPIA, a legal basis under GDPR Art. 9(2)(h) /
  national health-data law, a BAA-equivalent data processing agreement
  with any infrastructure provider, de-identification/pseudonymization
  before any non-clinical environment, and an audit log of every access
  to patient data. None of that is implemented here — it's out of scope
  for a local demo, but worth knowing before reusing this code against
  anything real.
