# Corruption & Repair Comparison Report

_Generated at: 2026-09-26T06:03:30.223565+00:00_

## 1. Metrics Comparison: Baseline vs Corrupted vs Repaired

| Metric | Baseline | Corrupted | Repaired |
| :--- | ---: | ---: | ---: |
| Retrieval Hit Rate | 100.0% | 80.0% | 100.0% |
| Mean Token F1 | 1.000 | 0.900 | 1.000 |
| Judge Accuracy | 100.0% | 90.0% | 100.0% |
| Mean Judge Score | 5.000 | 4.600 | 5.000 |

## 2. Data Quality Gate

| Stage | Quality Status | is_fresh |
| :--- | :---: | :---: |
| Corrupted | `False` | `False` |
| Repaired | `True` | `True` |

## 3. Nhan xet

- Sau khi bi tiem loi, Retrieval Hit Rate giam **20.0%** so voi baseline (hien tuong Silent Failure).
- Sau khi Repair tu raw snapshot, Retrieval Hit Rate phuc hoi them **20.0%** so voi trang thai corrupted.

