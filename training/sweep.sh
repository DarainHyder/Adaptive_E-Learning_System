#!/usr/bin/env bash
# Small hyper-parameter sweep for the transformer KT model on the ASSISTments benchmarks.
# Usage: bash training/sweep.sh [python]
set -u
PY=${1:-python}
cd "$(dirname "$0")/.."
mkdir -p training/logs/sweep
for ds in assist2009 assist2015; do
  for d in 64 128; do
    for layers in 1 2; do
      for drop in 0.2 0.4; do
        for lr in 1e-3 3e-4; do
          tag="_sweep_d${d}_l${layers}_p${drop}_lr${lr}"
          $PY training/train_kt.py --dataset $ds --model transformer --skip-bkt --epochs 80 --patience 8 \
            --d $d --layers $layers --heads 4 --dropout $drop --lr $lr --weight-decay 0.1 --tag "$tag" \
            > "training/logs/sweep/${ds}${tag}.log" 2>&1
          echo "$ds $tag $(grep 'TEST AUC' training/logs/sweep/${ds}${tag}.log)"
        done
      done
    done
  done
done
