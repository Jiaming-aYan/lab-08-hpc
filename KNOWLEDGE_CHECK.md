# Lab 08: Knowledge check

## 1. Slurm: what jobs have I submitted?

**Your answer:** I ran `sacct -S 2026-11-04 -X --format=JobID,JobName,NodeList,Partition,Account,User,State,Start,Elapsed` and saved the output in `results/job-history.txt`. It includes one-book tests, a cancelled array, and the final array `22767736`. All 94 tasks in that final array completed successfully. Earlier successful jobs covered the other seven unique books; one book was rerun. The final array used `gpu-a6000` because the `gpu-mig` queue was busy. `results/report.json` shows 101 of 101 books summarized.

## 2. Slurm: did every array task run at the same time?

**Your answer:** No. In array `22767736`, tasks 1–3 started at 12:38:48 on November 10, while tasks 92–94 started at 12:55:20. The 94 tasks took 16–25 seconds each. Slurm started tasks in batches as GPU resources became available, so their start times differ by more than 16 minutes.

## 3. Slurm: did my job use what it asked for?

**Your answer:** `results/seff.txt` reports that task `22767736_1` used 4.34 GB of memory, or 27.14% of the requested 16 GB. Its wall-clock time was 19 seconds, well below the requested five minutes. For a similar run, I would consider requesting 8 GB and two minutes per task, after checking the slowest and largest tasks to leave a safe margin.
