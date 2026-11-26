# Proposed schema registry design

!!! note
    This is the agreed design for [A03](https://github.com/ImperialCollegeLondon/FaraX/issues/3).
    Only the first slice is implemented (see
    [Implemented so far](#implemented-so-far)); the rest is still proposed.

## Implemented so far

`main.RegisteredSchema` stores a required display name and the parsed JSON definition.
Through Django Admin, an administrator uploads one JSON file and names the schema;
the add form's only content checks are that the file is no larger than the upload size
limit and parses as JSON (UTF-8, optional byte-order mark). Otherwise it reports an
error and registers nothing. The limit is the `SCHEMA_UPLOAD_MAX_BYTES` setting, read
from the `DJANGO_SCHEMA_UPLOAD_MAX_BYTES` environment variable (see the
[Developer Guide](index.md#schema-uploads)). The change page
shows the definition read-only. Names are trimmed, at most 255 characters, and unique
with case-sensitive comparison. The identifier is the model's automatic primary key.
Access uses Django Admin's standard add, view, change and delete permissions.

The definition is immutable: `RegisteredSchema.save()` raises a `ValidationError` with
code `immutable` if the definition differs from the stored one, and never writes the
definition column on an update. Definitions are compared as canonical JSON, so `1`,
`1.0` and `true` count as different. Bulk updates and direct SQL are not checked. The
name can be corrected through the change page. A registration with no dependants can be
deleted, and its name can then be registered again with a new identifier. No dependent
models exist yet, so there are no deletion rules beyond this; see
[Registrations and lifecycle](#registrations-and-lifecycle) for what they must do.

Not yet implemented: schema validation and draft handling (including draft
immutability), duplicate-key and non-standard number rejection, exact decimal numbers
and the upload size limit. Parts of the design below describing these are still proposals.

## Scope and permissions

The registry will let administrators upload JSON Schema documents through Django Admin
and make registered schemas available to other FaraX components. It will not add an
ingestion workflow, a public schema API, a dynamic data-entry form or a data-migration
system.

Schema management will use Django Admin's normal access controls: active staff members
need the relevant schema-model permissions, which appropriately configured superusers
have. Users without the required permissions must not be able to access the schema
management pages. [A02](https://github.com/ImperialCollegeLondon/FaraX/issues/2) can
map its Admin role to these permissions when that role is implemented. Restricting
management does not prevent authorised users from selecting schemas in future ingestion
and data-entry features; it does not automatically grant them access to full schema
documents.

## Registrations and lifecycle

Each Registered Schema represents one JSON Schema document and has a stable,
installation-local identifier. An administrator supplies a required display name.
Names are trimmed, limited to 255 characters after trimming, and unique among existing
registrations using case-sensitive comparisons. For example, `Co` and `CO` can be
different names. A deleted registration's name can be reused, but the new registration
gets a different identifier.

Administrators may correct a display name, but a registered definition and its
effective JSON Schema draft cannot be changed. A corrected definition or a different
draft requires a new registration. Normal application operations, including ordinary
model saves and Django Admin, must enforce this; direct SQL and bulk-update bypasses are
outside the PoC guarantee. See [ADR 0004](../adr/0004-immutable-registered-schemas.md).

Identical definitions may be registered under different names. Different definitions may
also declare the same JSON Schema `$id` or an equivalent identifier from an older draft;
FaraX's own identifier is separate from those declarations.

A schema can be deleted only when no currently stored record depends on it. If all
dependent records are later removed, deletion is permitted even if the schema was used
in the past. Future submission, workflow and other dependent models must protect their
schema references, for example with Django's `PROTECT`, and test that protection.

There is no retirement control, formal schema family or version number in A03. An
obsolete schema that is still referenced cannot be deleted and remains available to
future selection until a later lifecycle feature addresses it. The eventual strategy for
schema evolution and data migration remains a separate PoC decision.

## Upload and validation

Registration accepts one uploaded file, not a pasted-JSON editor. Validity depends on
the file contents, not its filename, extension or reported content type. The upload
must be UTF-8, with an optional UTF-8 byte-order mark. Malformed JSON, non-standard
numeric values and duplicate object keys anywhere in the document must be rejected with
a useful error.

The maximum upload size is configurable as a positive whole number of bytes through the
`DJANGO_SCHEMA_UPLOAD_MAX_BYTES` environment variable and a Django setting. The default
is 512,000 bytes, inclusive. Invalid configuration must be reported as an error rather
than silently replaced by the default.

The proposed implementation uses the `jsonschema` Python library to validate each
document as a schema against its applicable standard. It supports Draft 4, Draft 6,
Draft 7, Draft 2019-09 and Draft 2020-12. Unsupported or unrecognised declared drafts
are rejected. If `$schema` is absent, FaraX uses Draft 2020-12, records that effective
draft and tells the administrator. Boolean schemas are accepted where the effective
draft permits them.

The PoC will reject actual schema-reference keywords, including `$ref`, `$dynamicRef`
and `$recursiveRef` where they apply, even when they refer to definitions in the same
document. This rule must distinguish schema keywords from ordinary data: a field name
or example value containing `$ref` is not itself a schema reference. Draft
declarations, schema identifiers and ordinary URLs are not prohibited. Registration
must not fetch external resources.

This reference-free policy is stricter than JSON Schema. A valid schema using internal
or external references cannot be registered without adaptation or a later change to
the policy. Passing registration checks validates the schema document, not the
scientific correctness of its contents or any research data submitted against it.

## Persistence and retrieval

The database stores the parsed schema JSON and its effective draft, not the original
uploaded file bytes. Original whitespace, encoding and key order need not be preserved.
A schema upload is not a Raw File; Raw Files are research-data files submitted for
ingestion.

Numeric values must not silently change when a schema is stored or retrieved. Python
consumers receive decimal JSON numbers as `Decimal` values rather than binary floats.
The proposed implementation uses `simplejson` to encode and decode exact decimal
numbers. If a number cannot be preserved exactly, registration must fail with a clear
error. Schema validation and future consumers must handle these values and the recorded
draft correctly.

Django Admin displays the stored definition read-only and provides its ordinary action
history. A03 does not add separate creator, timestamp, description or category fields,
or promise a permanent audit trail.

## Verification and outstanding dependency

Automated tests should cover admin permissions, registration and retrieval, immutability,
name and deletion behaviour, each supported draft, invalid inputs, reference rejection,
exact numeric values and the upload-size boundary. Future issues must test deletion
protection against their actual dependent records.

The research team is expected to supply at least one real schema. Successfully
registering one remains an external acceptance criterion for A03; synthetic fixtures
alone cannot satisfy it.
