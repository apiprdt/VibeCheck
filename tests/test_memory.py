"""Tests for vibecheck's memory system."""

import pytest
from vibecheck.core.memory import (
    get_memory_context, record_concept, reset_memory,
    get_all_concepts, DB_DIR,
)
from pathlib import Path


@pytest.fixture
def clean_memory(tmp_path, monkeypatch):
    """Use a temp directory for vibecheck memory during tests."""
    test_dir = tmp_path / ".vibecheck"
    test_dir.mkdir()
    import vibecheck.core.memory as mem_module
    original_dir = mem_module.DB_DIR
    original_path = mem_module.DB_PATH
    mem_module.DB_DIR = test_dir
    mem_module.DB_PATH = test_dir / "knowledge.db"
    yield
    mem_module.DB_DIR = original_dir
    mem_module.DB_PATH = original_path


class TestMemoryProgression:
    def test_new_concept(self, clean_memory):
        concepts = ["SQL Injection Prevention"]
        statuses = get_memory_context(concepts)
        assert statuses["SQL Injection Prevention"] == "new"

    def test_reminder_after_first_exposure(self, clean_memory):
        record_concept("Test Concept", "file.py")
        statuses = get_memory_context(["Test Concept"])
        assert statuses["Test Concept"] == "reminder"

    def test_learned_after_multiple_exposures(self, clean_memory):
        record_concept("Test Concept", "file1.py")
        record_concept("Test Concept", "file2.py")
        statuses = get_memory_context(["Test Concept"])
        assert statuses["Test Concept"] == "learned"

    def test_reset_clears_all(self, clean_memory):
        record_concept("Concept A", "file.py")
        record_concept("Concept B", "file.py")
        count = reset_memory()
        assert count == 2
        all_concepts = get_all_concepts()
        assert len(all_concepts) == 0

    def test_get_all_concepts(self, clean_memory):
        record_concept("Concept A", "file1.py")
        record_concept("Concept B", "file2.py")
        all_concepts = get_all_concepts()
        names = {c["concept_name"] for c in all_concepts}
        assert "Concept A" in names
        assert "Concept B" in names


class TestMemoryEmpty:
    def test_empty_memory_context(self, clean_memory):
        statuses = get_memory_context([])
        assert statuses == {}

    def test_reset_empty_memory(self, clean_memory):
        count = reset_memory()
        assert count == 0
