# Midterm Mastery

## Part 1 (conceptual)
- `BSDS_Midterm_Mastery_Kunal_Juvvala.pdf` - MapReduce paper presentation

## Part 2 (empirical): evaluating the file transfer service
- **`Experiment_Presentation_Kunal_Juvvala.pdf` - the experiment presentation itself**
- `exp1-packet-loss/` - success rate and time vs. packet loss
- `exp2-file-size/` - success rate and time vs. file size
- `exp3-scaling/` - auto scaling under a stepped Locust load
- `scripts/` - every script used to run the tests
- `SERVICE_CHANGES.md` - what I changed in the service and why

Each experiment folder has `observations.md` (question, setup, prediction, results,
conclusions), the raw data, charts, and screenshots.

Test files are not committed (up to 4 MB each); `scripts/make_files.sh` recreates them.
