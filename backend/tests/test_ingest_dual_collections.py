"""Tests for dual collection ingestion logic."""
import pytest
from unittest.mock import MagicMock, patch
from qdrant_ingest.ingest_qdrant_contextual import (
    infer_document_type,
    infer_collection_name,
    load_all_chunks,
)


class TestInferDocumentType:
    """Tests for document type inference."""

    def test_normative_always_regulation(self):
        chunk = {"source_origin": "normative"}
        assert infer_document_type(chunk) == "regulation"

    def test_operational_faq(self):
        chunk = {"source_origin": "operational", "source_file": "faq-kt-tpp-2026.md"}
        assert infer_document_type(chunk) == "faq"

    def test_operational_stage(self):
        chunk = {"source_origin": "operational", "source_file": "1-shag-podacha-zayavki.md"}
        assert infer_document_type(chunk) == "stage_description"

    def test_operational_instruction(self):
        chunk = {"source_origin": "operational", "source_file": "7. instruction-po-samostoyatelnomu-podklyucheniyu.md"}
        assert infer_document_type(chunk) == "instruction"

    def test_operational_passport(self):
        chunk = {"source_origin": "operational", "source_file": "passport-tp-15-150kvt.md"}
        assert infer_document_type(chunk) == "instruction"

    def test_operational_pamyatka(self):
        chunk = {"source_origin": "operational", "source_file": "pamyatka-do-670kvt.md"}
        assert infer_document_type(chunk) == "infomaterial"

    def test_operational_default(self):
        chunk = {"source_origin": "operational", "source_file": "unknown-file.md"}
        assert infer_document_type(chunk) == "infomaterial"


class TestInferCollectionName:
    """Tests for collection name inference."""

    def test_normative_goes_to_normative_collection(self):
        chunk = {"source_origin": "normative"}
        result = infer_collection_name(chunk)
        assert result == "normative_documents"

    def test_operational_goes_to_operational_collection(self):
        chunk = {"source_origin": "operational"}
        result = infer_collection_name(chunk)
        assert result == "operational_content"

    def test_missing_source_origin_defaults_to_operational(self):
        chunk = {}
        result = infer_collection_name(chunk)
        assert result == "operational_content"
