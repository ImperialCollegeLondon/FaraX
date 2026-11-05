# Raw Files are kept in a File Store, not the database

Raw Files (JSON files under ~100 KB, or larger CSV files) are saved unchanged in a File
Store accessed through Django's storage API (the `STORAGES` setting). The database holds
only the data and metadata extracted from them. To start with, the File Store is
`FileSystemStorage`: a git-ignored `media/` directory locally and a named Docker volume
under Compose. Because the hosting target (ICT VM or Azure) is undecided, moving to
object storage such as Azure Blob later (via `django-storages`) should be a
configuration change, not a code change.

Keeping Raw Files out of the database is also needed for reproducibility: PostgreSQL's
`jsonb` drops duplicate keys and reorders keys, so the original file can't be recovered
from a `jsonb` column.

## Considered Options

- **Raw Files stored in PostgreSQL**: rejected because `jsonb` doesn't keep the original
  bytes and large CSV files would make the database much bigger.
- **Object storage from the start**: rejected while the hosting target is undecided.
  The storage API keeps this option open.
