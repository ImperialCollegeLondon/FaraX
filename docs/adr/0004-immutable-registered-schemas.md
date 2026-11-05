# Registered Schema definitions are immutable

In the proposed schema registry, a Registered Schema's JSON definition and effective
draft do not change after registration. A corrected definition or different draft
requires a new registration. A registration can be deleted only while no stored records
depend on it.

This prevents normal application operations from silently changing the schema used by
existing records, while allowing unused mistakes to be removed. Direct SQL and
bulk-update bypasses are outside this PoC guarantee. Formal versions, data migration and
retirement are deferred; this decision does not by itself guarantee complete
reproducibility.
