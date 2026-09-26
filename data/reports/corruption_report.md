# Corruption & Repair Comparison Report

_Generated at: 2026-09-26T04:27:05.288046+00:00_

## 1. Metrics Comparison: Baseline vs Corrupted vs Repaired

| Metric | Baseline | Corrupted | Repaired |
| :--- | ---: | ---: | ---: |
| Retrieval Hit Rate | 100.0% | 80.0% | 100.0% |
| Mean Token F1 | 0.520 | 0.417 | 0.520 |
| Judge Accuracy | 50.0% | 40.0% | 50.0% |
| Mean Judge Score | 3.000 | 2.600 | 3.000 |

## 2. Data Quality Gate

| Stage | Quality Status | is_fresh |
| :--- | :---: | :---: |
| Corrupted | `False` | `False` |
| Repaired | `True` | `True` |

## 3. Nhan xet

- Sau khi bi tiem loi, Retrieval Hit Rate giam **20.0%** so voi baseline (hien tuong Silent Failure).
- Sau khi Repair tu raw snapshot, Retrieval Hit Rate phuc hoi them **20.0%** so voi trang thai corrupted.

