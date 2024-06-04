"""SLURM preferences."""

scriptfn = {
    "qc": "marine_qc.py",
    "qc_hr": "marine_qc_hires.py",
}

nodesi = {
    "qc": 1,
    "qc_hr": 1,
}

TaskPNi = {
    "qc": 3,
    "qc_hr": 1,
}

ti = {"qc": "06:00:00", "qc_hr": "09:00:00"}

logdir = {
    "qc": "qc_log_directory",
    "qc_hr": "qc_hr_log_directory",
}

taskfile = {
    "qc": "qc.tasks",
    "qc_hr": "qc_hr.tasks",
}

slurmfile = {
    "qc": "qc.slurm",
    "qc_hr": "qc_hr.slurm",
}
