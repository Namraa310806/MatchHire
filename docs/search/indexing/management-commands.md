# Management Commands

## rebuild_search_index

Rebuilds index state for one or all entity types.

Examples:

- `python manage.py rebuild_search_index --entity-type candidate`
- `python manage.py rebuild_search_index --all --chunk-size 500 --progress`
- `python manage.py rebuild_search_index --all --dry-run`

## sync_search_index

Synchronizes index state incrementally or fully.

Examples:

- `python manage.py sync_search_index --entity-type job --since 1h`
- `python manage.py sync_search_index --all --full`
- `python manage.py sync_search_index --all --dry-run`
- `python manage.py sync_search_index --all --retry-dead-letter`

## verify_search_index

Validates index integrity against database state.

Examples:

- `python manage.py verify_search_index --entity-type resume --detailed`
- `python manage.py verify_search_index --all`
- `python manage.py verify_search_index --all --fix`

## search_index_status

Displays index health, counts, and telemetry.

Examples:

- `python manage.py search_index_status --entity-type candidate`
- `python manage.py search_index_status --all --metrics --jobs`
