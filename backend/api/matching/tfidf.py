"""Fixed-vocabulary TF-IDF cosine similarity over skill sets.

This is the ``skill_similarity`` signal (SPEC weight 0.50). It is a
pure-Python implementation — no NumPy, no scikit-learn — because the
vocabulary is fixed (~500 canonical skills) and sparse vectors are
small enough that dense linear algebra buys nothing.

Vocabulary construction
-----------------------
The vocabulary is the set of canonical skill names from the shared
skills dictionary (``api.extraction.skills_dictionary.json``,
version 1.0.0, 500+ terms). This is the SPEC "fixed vocabulary"
strategy: the same vocabulary is used for candidate and job vectors,
so vectors never go stale and no versioning is needed. Inputs may be
canonical names or aliases; aliases resolve to canonical names via
``SkillsDictionary.resolve_alias``. Terms outside the vocabulary are
ignored (SPEC: unknown skills are excluded from matching).

Term frequency
--------------
Inputs are *sets* of skills — duplicates carry no meaning (SPEC:
duplicate skills never change the score). Term frequency is therefore
binary: a present term has tf = 1.0, an absent term tf = 0.0.

Inverse document frequency
--------------------------
IDF requires a corpus. Two explicit vectorizer states exist:

- ``TfidfVectorizer.fit(corpus)`` — corpus-fitted TF-IDF. IDF is
  computed with sklearn-style smoothing over the supplied corpus of
  skill sets::

      idf(t) = ln((N + 1) / (df(t) + 1)) + 1

  where N = number of documents and df(t) = number of documents
  containing term t (unseen terms get df = 0, i.e. the maximum
  weight). ``is_corpus_fitted`` is True.

- ``TfidfVectorizer.uniform()`` / ``UNIFORM_VECTORIZER`` — every term
  weighs exactly 1.0. Cosine similarity over binary skill vectors.
  This is NOT corpus-fitted TF-IDF; it is the explicit opt-in for
  callers that have no corpus. ``is_corpus_fitted`` is False.
  ``fit(())`` (empty corpus) produces the same uniform weights.

``match()`` requires the caller to pass a vectorizer explicitly, so a
production scoring path cannot silently use uniform weights: the
caller must write ``vectorizer=UNIFORM_VECTORIZER`` (acknowledging
uniform behavior) or ``vectorizer=TfidfVectorizer.fit(job_corpus)``
(real TF-IDF). The integration gate fits the vectorizer once over the
active job skill corpus and injects it into scoring.

Normalization and cosine similarity
-----------------------------------
Each document vector is ``{term: tf * idf}`` restricted to the fixed
vocabulary. Cosine similarity is::

    dot(v1, v2) / (||v1|| * ||v2||)

Both-empty or either-empty input yields 0.0 (no NaN). Because all
weights are non-negative and finite, the result is always in [0, 1].
"""

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from api.extraction.skill_extractor import get_skills_dictionary

SparseVector = dict[str, float]


def normalize_skill_names(skill_names: Iterable[str]) -> frozenset[str]:
    """Resolve skill names/aliases to canonical vocabulary terms.

    Case-insensitive via the dictionary's alias resolution. Terms not
    in the fixed vocabulary are dropped. Order and duplicates do not
    affect the result.

    Raises:
        TypeError: if a non-string term is supplied.
    """
    dictionary = get_skills_dictionary()
    canonical: set[str] = set()
    for name in skill_names:
        if not isinstance(name, str):
            raise TypeError(
                f"skill names must be strings, got {type(name).__name__}"
            )
        resolved = dictionary.resolve_alias(name.strip())
        if resolved is not None:
            canonical.add(resolved[0])
    return frozenset(canonical)


@dataclass(frozen=True)
class TfidfVectorizer:
    """Fixed-vocabulary TF-IDF vectorizer for skill sets.

    Attributes:
        document_count: Number of corpus documents the IDF was fitted
            on. 0 means no corpus was fitted (uniform weights).
        doc_freq: Term -> number of corpus documents containing the term.
    """

    document_count: int = 0
    doc_freq: Mapping[str, int] = field(default_factory=dict)

    @classmethod
    def uniform(cls) -> "TfidfVectorizer":
        """Vectorizer with weight 1.0 for every term.

        Cosine similarity over binary skill vectors — explicitly NOT
        corpus-fitted TF-IDF. Use only when no corpus is available.
        """
        return cls()

    @property
    def is_corpus_fitted(self) -> bool:
        """True iff IDF was fitted on a non-empty corpus."""
        return self.document_count > 0

    @classmethod
    def fit(cls, corpus: Iterable[Iterable[str]]) -> "TfidfVectorizer":
        """Fit IDF statistics over a corpus of skill-name iterables.

        Each corpus document is normalized to canonical skill names
        before counting document frequency, so the same normalization
        rules apply to corpus and query inputs.
        """
        doc_freq: dict[str, int] = {}
        document_count = 0
        for document in corpus:
            terms = normalize_skill_names(document)
            document_count += 1
            for term in terms:
                doc_freq[term] = doc_freq.get(term, 0) + 1
        return cls(document_count=document_count, doc_freq=doc_freq)

    def term_weight(self, term: str) -> float:
        """Smoothed IDF weight for a canonical term.

        ``ln((N + 1) / (df + 1)) + 1`` where df defaults to 0 for terms
        absent from the fitted corpus. With N = 0 every term weighs 1.0.
        """
        df = self.doc_freq.get(term, 0)
        return math.log((self.document_count + 1) / (df + 1)) + 1.0

    def transform(self, skill_names: Iterable[str]) -> SparseVector:
        """Transform skill names into a sparse TF-IDF vector.

        Only canonical vocabulary terms appear; binary term frequency
        is multiplied by the term's IDF weight.
        """
        return {
            term: self.term_weight(term)
            for term in normalize_skill_names(skill_names)
        }


# Explicit uniform-weight vectorizer. Named UNIFORM (not DEFAULT) so
# it cannot be mistaken for corpus-fitted TF-IDF. match() requires a
# vectorizer argument, so callers must choose this or a fitted one.
UNIFORM_VECTORIZER = TfidfVectorizer.uniform()


def cosine_similarity(v1: SparseVector, v2: SparseVector) -> float:
    """Cosine similarity between two sparse vectors.

    Returns 0.0 when either vector is empty (never NaN).
    """
    if not v1 or not v2:
        return 0.0

    # Iterate over the smaller vector for the dot product
    if len(v1) > len(v2):
        v1, v2 = v2, v1

    dot = sum(weight * v2.get(term, 0.0) for term, weight in v1.items())
    norm1 = math.sqrt(sum(w * w for w in v1.values()))
    norm2 = math.sqrt(sum(w * w for w in v2.values()))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def skill_similarity(
    candidate_skills: Iterable[str],
    job_skills: Iterable[str],
    vectorizer: TfidfVectorizer = UNIFORM_VECTORIZER,
) -> float:
    """TF-IDF cosine similarity between candidate and job skill sets.

    The low-level component helper defaults to ``UNIFORM_VECTORIZER``
    for convenience; ``match()`` has no such default and requires an
    explicit vectorizer.
    """
    return cosine_similarity(
        vectorizer.transform(candidate_skills),
        vectorizer.transform(job_skills),
    )
