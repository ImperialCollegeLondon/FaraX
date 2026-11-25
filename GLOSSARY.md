# FaraX

FaraX is a data management platform for synthesisability in data-driven materials
discovery. It ingests, validates, stores and visualises research data.

## Language

**Staff**:
A user account that can access Django's Admin page. Staff can only do what their permissions allow, so a staff user with no permissions can log in but cannot manage anything.

**Admin**:
A staff user in the Admin group who can manage user accounts and registered
schemas but cannot manage superuser accounts.

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
It is registered by an administrator uploading a JSON file; only the parsed JSON is
stored, and the upload is not a Raw File.
