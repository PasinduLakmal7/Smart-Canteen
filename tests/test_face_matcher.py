"""
Unit tests for FaceMatcher, Vector Similarity, and Threshold Decisions in Phase 4.
"""

import pytest
import numpy as np

from src.face_recognition.matcher import FaceMatcher


def test_cosine_similarity_identical_and_orthogonal():
    matcher = FaceMatcher(default_threshold=0.60)

    vec_a = [1.0, 0.0, 0.0]
    vec_b = [1.0, 0.0, 0.0]
    assert pytest.approx(matcher.cosine_similarity(vec_a, vec_b), rel=1e-3) == 1.0

    vec_c = [0.0, 1.0, 0.0]
    assert pytest.approx(matcher.cosine_similarity(vec_a, vec_c), rel=1e-3) == 0.0


def test_find_best_match_known_employee():
    matcher = FaceMatcher(default_threshold=0.60)

    # Gallery
    gallery = [
        {"employee_id": 1, "employee_code": "EMP001", "embedding": [0.9, 0.1, 0.0], "sample_tag": "frontal"},
        {"employee_id": 2, "employee_code": "EMP002", "embedding": [0.1, 0.9, 0.0], "sample_tag": "frontal"},
    ]

    # Query matching EMP001
    query = [0.88, 0.12, 0.0]
    is_match, top_match, ranked = matcher.find_best_match(query, gallery, threshold=0.60)

    assert is_match is True
    assert top_match is not None
    assert top_match.employee_code == "EMP001"
    assert top_match.similarity > 0.90


def test_find_best_match_unknown_person_rejected():
    matcher = FaceMatcher(default_threshold=0.60)

    gallery = [
        {"employee_id": 1, "employee_code": "EMP001", "embedding": [0.9, 0.1, 0.0], "sample_tag": "frontal"},
    ]

    # Query is completely different (orthogonal)
    unknown_query = [0.0, 0.0, 1.0]
    is_match, top_match, ranked = matcher.find_best_match(unknown_query, gallery, threshold=0.60)

    assert is_match is False
    assert top_match.similarity < 0.60


def test_benchmark_evaluation_metrics():
    matcher = FaceMatcher()
    genuine = [
        ([0.9, 0.1], [0.89, 0.11]),
        ([0.1, 0.9], [0.12, 0.88]),
    ]
    impostor = [
        ([0.9, 0.1], [0.1, 0.9]),
    ]

    report = matcher.evaluate_threshold(genuine, impostor, threshold=0.60)
    assert report.total_samples == 3
    assert report.accuracy == 1.0
    assert report.false_acceptance_rate == 0.0
    assert report.false_rejection_rate == 0.0
