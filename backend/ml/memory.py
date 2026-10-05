"""
Forgetting model used for spaced repetition.

Recall probability decays exponentially, R = exp(-days / S), where the memory
stability S (in days) grows with successful practice and mastery, the same shape as
half-life regression (Settles & Meeder, 2016) with hand-set coefficients.

Forgetting is applied at *read* time to produce an "effective" mastery; it is never
written back to the database, so repeated reads don't compound decay.
"""
import math
from datetime import datetime

REVIEW_RECALL_THRESHOLD = 0.7


def stability_days(practice_count, correct_count, mastery):
    correct_count = correct_count or 0
    practice_count = practice_count or 0
    wrong = max(0, practice_count - correct_count)
    return max(0.5, 1.0 + 1.6 * correct_count ** 0.85 - 0.3 * wrong ** 0.7) * (0.5 + mastery)


def recall_probability(last_practiced, practice_count, correct_count, mastery, now=None):
    if not last_practiced or not practice_count:
        return 1.0
    now = now or datetime.utcnow()
    days = max(0.0, (now - last_practiced).total_seconds() / 86400)
    return math.exp(-days / stability_days(practice_count, correct_count, mastery))


def effective_mastery(mastery, recall):
    # Forgotten knowledge is easier to relearn than new material, so it never decays to zero.
    return mastery * (0.35 + 0.65 * recall)


def days_until_review(practice_count, correct_count, mastery, threshold=REVIEW_RECALL_THRESHOLD):
    return -math.log(threshold) * stability_days(practice_count, correct_count, mastery)
