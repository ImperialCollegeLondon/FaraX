# Single repository for all components

FaraX is expected to grow several independently deployable components: the Django API
and admin, a user interface (Streamlit, see A06) and containerised ingestion workflows
(see A04). We keep them all in this one repository. The Django project lives at the root
and the other components get their own top-level directories (e.g. `ui/`, `workflows/`)
with their own Dockerfiles as they are introduced. Independent deployment comes from
separate container images, not separate repositories. This keeps changes that cut across
components in a single pull request and reduces overhead for a small team.

## Considered Options

- **One repository per component**: rejected for now. Coordinating changes across
  repositories (e.g. a schema change that touches the API and a workflow) adds release
  and review overhead that a small team doesn't need. A component can still be split out
  later if it acquires its own team or release cycle.
