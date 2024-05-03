f"#!/bin/bash"
f"#SBATCH --job-name={sid_dck}.job"
f"#SBATCH --output={log_diri}/%a.out"
f"#SBATCH --error={log_diri}/%a.err"
f"#SBATCH --time={ti}"
f"#SBATCH --nodes={nodesi}"
f"#SBATCH --open-mode=truncate"
f"#SBATCH --account=p200307"
f"#SBATCH --partition=cpu"
f"#SBATCH --qos=default"
f"#SBATCH --cpus-per-task=1"
f"module load taskfarm"
f"export TASKFARM_PPN={TaskPNi}"
f"taskfarm {taskfarm_file}"
