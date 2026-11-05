# FaraX

FaraX is a data management platform for synthesisability in data-driven materials
discovery. It ingests, validates, stores and visualises research data.

## Language

**Raw File**:
A research-data file exactly as uploaded by a user for ingestion, before any processing.
It is never modified after upload.
_Avoid_: Artifact, raw data, upload

**File Store**:
The place where Raw Files are kept, separate from the database.
_Avoid_: Datastore, blob store

**Registered Schema**:
A definition of the permitted structure and content of research data that is available
for use in FaraX.
