#!/bin/bash
#SBATCH --account=ds2022
#SBATCH --job-name=summarize
#SBATCH --partition=gpu-mig
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:05:00
#SBATCH --array=1-101
#SBATCH --output=logs/summarize-%A_%a.out

source ~/.bashrc
set -euo pipefail
export HF_HUB_OFFLINE=1
module load uv
uv run python src/book_analysis/summarize.py "$1" "$SLURM_ARRAY_TASK_ID"
