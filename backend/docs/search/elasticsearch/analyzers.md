# Elasticsearch Analyzers

## Overview

Elasticsearch analyzers process text before it is indexed and searched. The MatchHire Elasticsearch provider includes custom analyzers optimized for recruitment search scenarios.

## Analyzer Components

An analyzer consists of:
1. **Tokenizer**: Breaks text into individual tokens
2. **Character Filters**: Pre-process characters before tokenization
3. **Token Filters**: Post-process tokens after tokenization

## Built-in Analyzers

### Standard Analyzer

The standard analyzer is the default analyzer for most text fields.

```python
"standard": {
    "type": "standard",
    "stopwords": "_english_"
}
```

**Features:**
- Splits words at word boundaries
- Removes most punctuation
- Lowercases tokens
- Removes English stopwords

**Use Cases:**
- General full-text search
- Description fields
- Bio fields
- Summary fields

### Lowercase Analyzer

A simple analyzer that only lowercases text.

```python
"lowercase": {
    "type": "custom",
    "tokenizer": "standard",
    "filter": ["lowercase"]
}
```

**Features:**
- Splits words at word boundaries
- Lowercases tokens
- No stopwords removal

**Use Cases:**
- Case-insensitive exact matching
- Normalizing input before processing

### ASCII Folding Analyzer

Converts Unicode characters to ASCII equivalents.

```python
"ascii_folding": {
    "type": "custom",
    "tokenizer": "standard",
    "filter": ["lowercase", "asciifolding"]
}
```

**Features:**
- Converts accented characters to ASCII
- Lowercases tokens
- Removes diacritics

**Use Cases:**
- Handling international names
- Matching "café" with "cafe"
- Normalizing non-ASCII text

### Edge N-gram Analyzer

Generates edge n-grams for autocomplete.

```python
"edge_ngram_analyzer": {
    "type": "custom",
    "tokenizer": "edge_ngram_tokenizer",
    "filter": ["lowercase"]
}
```

**Features:**
- Generates prefixes of words
- Min gram: 2 characters
- Max gram: 20 characters
- Only letter and digit characters

**Use Cases:**
- Autocomplete suggestions
- Prefix matching
- Type-ahead search

**Example:**
- Input: "software"
- Output: ["so", "sof", "soft", "softw", "softwa", "softwar", "software"]

### Autocomplete Analyzer

Optimized for autocomplete with single-character prefixes.

```python
"autocomplete_analyzer": {
    "type": "custom",
    "tokenizer": "autocomplete_tokenizer",
    "filter": ["lowercase", "asciifolding"]
}
```

**Features:**
- Generates prefixes starting from 1 character
- Includes ASCII folding for international support
- Lowercases tokens

**Use Cases:**
- Fast autocomplete
- International autocomplete
- Mobile-friendly autocomplete

### Search Analyzer

Used for searching against edge n-gram indexed fields.

```python
"search_analyzer": {
    "type": "custom",
    "tokenizer": "standard",
    "filter": ["lowercase", "asciifolding"]
}
```

**Features:**
- Standard tokenization
- Lowercases tokens
- ASCII folding for international support

**Use Cases:**
- Searching against edge n-gram fields
- Normalizing search queries
- International search

### Synonym Analyzer

Supports synonym expansion (placeholder for future use).

```python
"synonym_analyzer": {
    "type": "custom",
    "tokenizer": "standard",
    "filter": ["lowercase", "synonym_filter"]
}
```

**Features:**
- Standard tokenization
- Lowercases tokens
- Expands synonyms

**Use Cases:**
- Matching "JS" with "JavaScript"
- Matching "Python" with "Py"
- Matching "TS" with "TypeScript"

**Current Status:** Placeholder with empty synonym list. Can be configured at runtime.

## Tokenizers

### Edge N-gram Tokenizer

```python
"edge_ngram_tokenizer": {
    "type": "edge_ngram",
    "min_gram": 2,
    "max_gram": 20,
    "token_chars": ["letter", "digit"]
}
```

**Parameters:**
- `min_gram`: Minimum n-gram length (2)
- `max_gram`: Maximum n-gram length (20)
- `token_chars`: Characters to include (letters, digits)

### Autocomplete Tokenizer

```python
"autocomplete_tokenizer": {
    "type": "edge_ngram",
    "min_gram": 1,
    "max_gram": 20,
    "token_chars": ["letter", "digit"]
}
```

**Parameters:**
- `min_gram`: Minimum n-gram length (1)
- `max_gram`: Maximum n-gram length (20)
- `token_chars`: Characters to include (letters, digits)

## Token Filters

### Synonym Filter

```python
"synonym_filter": {
    "type": "synonym",
    "synonyms": [
        # Placeholder for future synonym configuration
        # "js, javascript",
        # "ts, typescript",
        # "py, python",
    ]
}
```

**Usage:**
```python
from apps.search.providers.elasticsearch.analyzers import Analyzers

# Add a synonym
Analyzers.add_synonym("js, javascript")

# Set all synonyms
Analyzers.set_synonyms([
    "js, javascript",
    "ts, typescript",
    "py, python",
    "golang, go",
])

# Get current synonyms
synonyms = Analyzers.get_synonyms()
```

### English Stopwords Filter

```python
"english_stopwords": {
    "type": "stop",
    "stopwords": "_english_"
}
```

**Features:**
- Removes common English stopwords
- Improves search relevance
- Reduces index size

### English Stemmer Filter

```python
"english_stemmer": {
    "type": "stemmer",
    "name": "english"
}
```

**Features:**
- Reduces words to root form
- Matches "running" with "run"
- Improves recall

### English Possessive Filter

```python
"english_possessive": {
    "type": "stemmer",
    "name": "possessive_english"
}
```

**Features:**
- Removes possessive apostrophes
- Matches "John's" with "John"
- Handles proper nouns

## Normalizers

Normalizers are used for keyword fields to normalize values before indexing.

### Lowercase Normalizer

```python
"lowercase_normalizer": {
    "type": "custom",
    "filter": ["lowercase"]
}
```

**Use Cases:**
- Normalizing email addresses
- Normalizing URLs
- Case-insensitive keyword matching

### ASCII Normalizer

```python
"ascii_normalizer": {
    "type": "custom",
    "filter": ["lowercase", "asciifolding"]
}
```

**Use Cases:**
- International keyword matching
- Normalizing company names
- Normalizing location names

### Keyword Normalizer

```python
"keyword_normalizer": {
    "type": "custom",
    "filter": ["lowercase", "asciifolding"],
    "char_filter": []
}
```

**Use Cases:**
- General keyword normalization
- Consistent keyword indexing
- Case-insensitive exact matching

## Analyzer Selection Guide

### When to Use Standard Analyzer
- General full-text search
- Description fields
- Bio fields
- Summary fields

### When to Use Edge N-gram Analyzer
- Autocomplete fields
- Title fields
- Name fields
- Company name fields

### When to Use ASCII Folding Analyzer
- International content
- Names with accents
- Mixed-language content

### When to Use Synonym Analyzer
- Skill matching
- Technology synonyms
- Industry terminology

### When to Use Search Analyzer
- Searching against edge n-gram fields
- Normalizing user queries
- International search

## Performance Considerations

### Index Size
- Edge n-gram analyzers increase index size significantly
- Consider using edge n-gram only on essential fields
- Use autocomplete analyzer with min_gram=1 for smaller n-grams

### Query Performance
- Standard analyzer is fastest for full-text search
- Edge n-gram queries are slower due to more terms
- Synonym expansion increases query complexity

### Memory Usage
- Complex analyzers use more memory
- Consider caching for frequently used analyzers
- Monitor JVM heap usage

## Configuration Examples

### Custom Synonyms

```python
from apps.search.providers.elasticsearch.analyzers import Analyzers

# Configure synonyms for technology matching
Analyzers.set_synonyms([
    "js, javascript, ecmascript",
    "ts, typescript",
    "py, python",
    "rb, ruby",
    "golang, go",
    "c#, csharp",
    "c++, cpp",
])

# Add a single synonym
Analyzers.add_synonym("ml, machine learning")
```

### Custom Analyzer Settings

```python
from apps.search.providers.elasticsearch.analyzers import Analyzers

# Modify edge n-gram settings
Analyzers.ANALYSIS_SETTINGS["analysis"]["tokenizer"]["edge_ngram_tokenizer"]["min_gram"] = 3
Analyzers.ANALYSIS_SETTINGS["analysis"]["tokenizer"]["edge_ngram_tokenizer"]["max_gram"] = 15
```

### Custom Index Settings

```python
from apps.search.providers.elasticsearch.analyzers import Analyzers

# Get settings with custom configuration
custom_settings = {
    "number_of_shards": 5,
    "number_of_replicas": 2,
    "refresh_interval": "5s"
}

settings = Analyzers.get_index_settings(custom_settings)
```

## Best Practices

1. **Use standard analyzer** for general full-text search
2. **Use edge n-gram** only for autocomplete fields
3. **Configure synonyms** for domain-specific terminology
4. **Use ASCII folding** for international content
5. **Monitor index size** with edge n-gram analyzers
6. **Test analyzer output** before production use
7. **Use search analyzer** for querying edge n-gram fields
8. **Configure appropriate n-gram lengths** for your data

## Testing Analyzers

You can test analyzer output using the Elasticsearch analyze API:

```python
# Test edge n-gram analyzer
response = client.indices.analyze(
    index="matchhire_job",
    body={
        "analyzer": "edge_ngram_analyzer",
        "text": "software engineer"
    }
)

# Test synonym analyzer
response = client.indices.analyze(
    index="matchhire_job",
    body={
        "analyzer": "synonym_analyzer",
        "text": "javascript developer"
    }
)
```

## Future Enhancements

### Planned Features
- Phonetic matching (soundex, metaphone)
- Shingle filters for phrase matching
- Keep words filter for preserving important terms
- Pattern-based tokenizers
- Custom character filters
- Language-specific analyzers

### Extension Points
- Custom synonym management
- Dynamic analyzer configuration
- Per-field analyzer selection
- Analyzer chains
