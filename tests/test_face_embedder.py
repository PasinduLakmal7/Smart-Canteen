"""
Unit tests for FaceEmbedder and 128D Feature Extraction in Phase 4.
"""

import pytest
import numpy as np

from src.face_recognition.embedder import FaceEmbedder


def test_face_embedder_dimension_and_norm():
    embedder = FaceEmbedder(embedding_dim=128)
    face_crop = np.random.randint(50, 200, (112, 112, 3), dtype=np.uint8)

    embedding = embedder.extract_embedding(face_crop)
    assert len(embedding) == 128
    assert all(isinstance(x, float) for x in embedding)

    # Check L2 unit norm
    norm = np.linalg.norm(np.array(embedding))
    assert pytest.approx(norm, rel=1e-3) == 1.0


def test_face_embedder_deterministic_output():
    embedder = FaceEmbedder(embedding_dim=128)
    face_crop = np.zeros((112, 112, 3), dtype=np.uint8)
    face_crop[30:80, 30:80] = 200

    emb1 = embedder.extract_embedding(face_crop)
    emb2 = embedder.extract_embedding(face_crop)

    assert emb1 == emb2


def test_face_embedder_empty_input():
    embedder = FaceEmbedder(embedding_dim=128)
    empty = np.array([])
    res = embedder.extract_embedding(empty)
    assert len(res) == 128
    assert all(x == 0.0 for x in res)
