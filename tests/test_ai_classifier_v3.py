"""
Domain classifier V3: accuracy regression gate, test-set integrity and
explainability guarantees (see docs/AI_GOVERNANCE.md, section 3.1).
"""
import importlib.util
import re
import sys
from pathlib import Path

import pytest

from backend.app.services.ai.classification_service import (
    REVIEW_CONFIDENCE_THRESHOLD, AIClassificationService,
)

ROOT = Path(__file__).resolve().parent.parent

# Held-out TEST result recorded in ai_accuracy_report.json for V3.0.0
# (178/198). CI fails if accuracy drops more than 2 points below it.
TEST_ACCURACY_BASELINE = 0.899
DEV_ACCURACY_BASELINE = 0.973
ALLOWED_DROP = 0.02
MIN_DOMAIN_ACCURACY = 0.65
# SHA-256 of the 198 held-out TEST reports frozen since commit cc2bbfc.
TEST_SET_SHA256 = "567427daf2523b6d0ca8451d36bb0704af3731c3d0ccc788583823e8081577a1"


@pytest.fixture(scope="module")
def bench():
    spec = importlib.util.spec_from_file_location("ai_accuracy_benchmark", ROOT / "scripts" / "ai_accuracy_benchmark.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ai_accuracy_benchmark"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def keywords_only():
    return AIClassificationService(embeddings=False)


def _norm(item):
    return re.sub(r"\W+", " ", f"{item['title']} {item['description']}".lower()).strip()


def test_heldout_test_set_is_frozen(bench):
    assert len(bench.SAMPLES) == 198
    assert bench.fingerprint_test_set() == TEST_SET_SHA256, (
        "The held-out TEST reports changed. They must stay frozen; add new "
        "examples to scripts/ai_eval/train_dev.jsonl instead."
    )


def test_train_dev_and_test_splits_do_not_overlap(bench):
    train, dev = bench.load_train_dev()
    assert len(train) > len(bench.SAMPLES) and len(dev) > 0
    test_texts = {_norm(s) for s in bench.SAMPLES}
    test_titles = {s["title"].lower() for s in bench.SAMPLES}
    for item in train + dev:
        assert _norm(item) not in test_texts
        assert item["title"].lower() not in test_titles
    assert not {_norm(s) for s in train} & {_norm(s) for s in dev}


def test_heldout_accuracy_does_not_regress(bench):
    result = bench.evaluate(bench.SAMPLES)
    assert result["accuracy"] >= TEST_ACCURACY_BASELINE - ALLOWED_DROP, result["accuracy_pct"]
    for domain, stats in result["per_domain"].items():
        assert stats["accuracy"] >= MIN_DOMAIN_ACCURACY, f"{domain}: {stats}"


def test_dev_accuracy_does_not_regress(bench):
    _, dev = bench.load_train_dev()
    assert bench.evaluate(dev)["accuracy"] >= DEV_ACCURACY_BASELINE - ALLOWED_DROP


def test_prediction_explains_itself(keywords_only):
    out = keywords_only.classify(
        "Handpump broken in tola",
        "The only hand pump has given no drinking water for two weeks.",
    ).output
    assert out["domain"] == "Water Resources"
    assert {"handpump", "drinking water"} <= set(out["matched_keywords"])
    signal = out["matched_signals"][0]
    assert set(signal) == {"term", "domain", "weight", "field", "negated"}
    assert 0.0 < out["confidence"] <= 0.96
    assert out["review_threshold"] == REVIEW_CONFIDENCE_THRESHOLD
    assert out["method"] == "keywords"


def test_word_boundaries_prevent_substring_false_positives(keywords_only):
    # "lac" must not fire inside "black"/"place", nor "tree" inside "street".
    out = keywords_only.classify("Black smoke near the street", "The place is covered in factory smoke.").output
    assert out["domain"] == "Environment"
    terms = {s["term"] for s in out["matched_signals"]}
    assert "lac" not in terms and "tree" not in terms


def test_topic_negation_discounts_negated_domain(keywords_only):
    out = keywords_only.classify(
        "Not a road problem, it is the water pipeline under it",
        "The road surface itself is fine; the pipeline leaks and the street has no water supply.",
    ).output
    assert out["domain"] == "Water Resources"
    title_road = [s for s in out["matched_signals"] if s["term"] == "road" and s["field"] == "title"]
    assert title_road and title_road[0]["negated"] is True


@pytest.mark.parametrize("text", [
    "There is no doctor at the PHC",
    "There is not a single doctor at the PHC",
    "Village without electricity since Monday",
])
def test_absence_is_not_treated_as_negation(keywords_only, text):
    out = keywords_only.classify(text, "").output
    assert out["matched_signals"] and not any(s["negated"] for s in out["matched_signals"])


def test_hinglish_and_devanagari_terms(keywords_only):
    assert keywords_only.classify("bijli nahi hai", "transformer jal gaya 3 din se").output["domain"] == "Energy"
    assert keywords_only.classify("गांव में रोजगार नहीं", "युवा पलायन कर रहे हैं").output["domain"] == "Rural Livelihoods"
    assert keywords_only.classify("aspatal me dawai nahi", "").output["domain"] == "Healthcare"


def test_low_confidence_goes_to_human_review(keywords_only):
    # Evenly split evidence (road vs water) leaves no margin over the runner-up.
    out = keywords_only.classify("Road and water", "").output
    assert out["confidence"] < REVIEW_CONFIDENCE_THRESHOLD
    assert out["requires_human_review"] is True
    assert out["runner_up_domain"] is not None

    unknown = keywords_only.classify("xkq zzy plerm", "qbnf trzl").output
    assert unknown["domain"] == "Unclassified" and unknown["requires_human_review"] is True


class _FakeEmbeddings:
    """Maps text to a one-hot vector on the domain whose description it shares words with."""

    def __init__(self, available=True, fail=False):
        self.available, self.fail = available, fail

    def is_available(self):
        return self.available

    def embed(self, texts):
        if self.fail:
            return None
        return [[1.0 if "sanitation" in t.lower() or "toilet" in t.lower() else 0.0, 1.0] for t in texts]


def test_embedding_blend_when_model_available(monkeypatch):
    monkeypatch.setattr(sys.modules["backend.app.services.ai.classification_service"], "embedding_service",
                        _FakeEmbeddings())
    result =AIClassificationService().classify("Community toilet locked", "Women have nowhere to go.")
    assert result.output["method"] == "keywords+embeddings"
    assert result.output["domain"] == "Sanitation"
    assert result.output["matched_keywords"]
    assert result.is_fallback is False
    assert result.features_json["embedding_similarities"]


@pytest.mark.parametrize("fake", [_FakeEmbeddings(available=False), _FakeEmbeddings(fail=True)])
def test_embedding_unavailable_falls_back_to_keywords(monkeypatch, fake):
    monkeypatch.setattr(sys.modules["backend.app.services.ai.classification_service"], "embedding_service", fake)
    result = AIClassificationService().classify("Community toilet locked", "Women have nowhere to go.")
    assert result.output["method"] == "keywords"
    assert result.output["domain"] == "Sanitation"
    assert result.is_fallback is True
