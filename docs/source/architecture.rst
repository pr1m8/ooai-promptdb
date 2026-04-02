Architecture
============

Purpose
-------

Prompt-heavy LLM applications often end up with a messy mix of inline strings,
YAML files, half-versioned edits, and manual environment promotion. **promptdb**
provides a clean separation:

- **Prompt definitions and version metadata** live in a relational database.
- **Large bundles and artifacts** live in local blob storage or MinIO.
- **LangChain-compatible prompt objects** are materialized at runtime.
- **Aliases like** ``production`` **or** ``staging`` point at immutable
  versions — promotion is an alias move, not a code change.
- **Files remain first-class** so prompts can stay in source control.

System overview
---------------

.. mermaid::

   flowchart TB
       subgraph Authoring
           FILES[YAML / JSON / .txt files]
           CLI[Rich CLI]
           API[FastAPI API]
           DASH[Streamlit Dashboard]
       end

       subgraph Core
           CLIENT[PromptClient]
           SERVICE[PromptService]
       end

       subgraph Persistence
           DB[(SQLAlchemy<br/>Postgres / SQLite)]
           BLOB[(BlobStore<br/>Local / MinIO)]
       end

       subgraph Runtime
           LC[LangChain<br/>PromptTemplate /<br/>ChatPromptTemplate]
           LG[LangGraph<br/>Agent Nodes]
       end

       FILES --> CLIENT
       CLI --> CLIENT
       API --> SERVICE
       DASH --> SERVICE
       CLIENT --> SERVICE
       SERVICE --> DB
       SERVICE --> BLOB
       CLIENT --> LC
       LC --> LG

Prompt lifecycle
----------------

.. mermaid::

   sequenceDiagram
       participant Author
       participant Client as PromptClient
       participant Service as PromptService
       participant DB as Database
       participant Blob as BlobStore

       Author->>Client: register_text() or register_file()
       Client->>Service: register(PromptRegistration)
       Service->>DB: create_version()
       Service->>DB: move_alias("production")
       Service-->>Client: PromptVersionView

       Author->>Client: get("ns/name:production")
       Client->>Service: resolve(PromptRef)
       Service->>DB: resolve(selector)
       Service-->>Client: PromptVersionView
       Client-->>Author: ResolvedPrompt

       Author->>Client: resolved.render_text(vars)
       Client-->>Author: rendered string

       Author->>Client: resolved.as_langchain()
       Client-->>Author: LangChain PromptTemplate

Version and alias model
-----------------------

.. mermaid::

   graph LR
       P[Prompt<br/>support/triage] --> V1[Version rev:1<br/>spec_hash: abc...]
       P --> V2[Version rev:2<br/>spec_hash: def...]
       P --> V3[Version rev:3<br/>spec_hash: ghi...]

       A_PROD[Alias: production] --> V2
       A_STAGING[Alias: staging] --> V3
       A_LATEST[Alias: latest] --> V3

       style A_PROD fill:#2d6,stroke:#333
       style A_STAGING fill:#f90,stroke:#333
       style A_LATEST fill:#69f,stroke:#333

Versions are **immutable**. Aliases are **movable pointers**. Promoting a
version to production is just an alias move — no code changes needed.

Layer diagram
-------------

.. code-block:: text

   files / CLI / API / dashboard
             |
         PromptClient (client.py)  — ergonomic facade
             |
         PromptService (service.py) — orchestrates workflows
          /          \
   PromptRepository   BlobStore adapters
   (db.py)            (storage.py)
   SQLAlchemy ORM     LocalBlobStore | MinioBlobStore

Key modules
-----------

**domain.py**
  Core Pydantic models: ``PromptSpec``, ``PromptRef``, ``PromptVersionView``,
  ``ResolvedPrompt``, ``PromptRenderResult``. All rendering logic lives here.
  Supports f-string, Jinja2, and mustache template formats.

**db.py**
  SQLAlchemy ORM tables (``prompts``, ``prompt_versions``, ``prompt_aliases``,
  ``prompt_assets``) and ``PromptRepository`` for persistence and resolution.

**service.py**
  ``PromptService`` coordinates registration, alias movement, resolution,
  rendering, and export. Shared by API and CLI.

**client.py**
  ``PromptClient`` facade. ``PromptClient.from_env()`` creates a fully wired
  instance from ``PROMPTDB_*`` environment variables.

**api.py**
  FastAPI app factory (``create_app``). Routes under ``/api/v1/``.

**storage.py**
  ``LocalBlobStore`` (filesystem) and ``MinioBlobStore`` (S3-compatible).

**files.py**
  Load prompts from ``.yaml`` / ``.json`` / ``.txt`` / ``.md`` files; write
  specs and version bundles back.

**cli.py**
  Rich-powered CLI: ``promptdb init | list | register-file | resolve | render | export-file``.

**settings.py**
  ``AppSettings`` reads ``PROMPTDB_*`` environment variables. Defaults to
  SQLite + local blob storage.

Prompt references
-----------------

References follow the compact ``namespace/name:selector`` format:

- ``support/triage:production`` — resolve via alias
- ``support/triage:rev:2`` — resolve via revision number
- ``support/triage:latest`` — highest revision (default)
- ``support/triage:2026.04.01.1`` — resolve via user_version label
- ``support/triage:<uuid>`` — resolve via version ID

Resolution order
----------------

.. mermaid::

   flowchart TD
       START[selector] --> UUID{Exact UUID match?}
       UUID -->|yes| DONE[Return version]
       UUID -->|no| REV{Starts with rev:N?}
       REV -->|yes| REVLOOKUP[Lookup by revision number]
       REVLOOKUP --> DONE
       REV -->|no| ALIAS{Alias match?}
       ALIAS -->|yes| ALIASLOOKUP[Follow alias pointer]
       ALIASLOOKUP --> DONE
       ALIAS -->|no| UV{user_version match?}
       UV -->|yes| DONE
       UV -->|no| LATEST{selector == latest?}
       LATEST -->|yes| LATESTLOOKUP[Highest revision]
       LATESTLOOKUP --> DONE
       LATEST -->|no| ERR[LookupError]

Database schema
---------------

.. mermaid::

   erDiagram
       prompts {
           string id PK
           string namespace
           string name
           datetime created_at
       }
       prompt_versions {
           string id PK
           string prompt_id FK
           int revision
           string user_version
           text spec_json
           string spec_hash
           string created_by
           datetime created_at
       }
       prompt_aliases {
           string id PK
           string prompt_id FK
           string alias
           string version_id FK
           datetime updated_at
       }
       prompt_assets {
           string id PK
           string version_id FK
           string kind
           string storage_backend
           string bucket
           string object_key
           string content_type
           int byte_size
           string checksum_sha256
           text metadata_json
           datetime created_at
       }

       prompts ||--o{ prompt_versions : "has"
       prompts ||--o{ prompt_aliases : "has"
       prompt_versions ||--o{ prompt_assets : "has"
       prompt_aliases }o--|| prompt_versions : "points to"

Persistence split
-----------------

- **Database**: prompt identities, versions, aliases, and relational asset
  metadata.
- **Blob store**: exported bundles and larger artifacts. Every blob object has
  a matching ``prompt_assets`` row so metadata remains queryable via SQL.

Alembic migrations
------------------

Schema changes are managed with Alembic. Run migrations before production
startup:

.. code-block:: bash

   alembic upgrade head

Migration files live in ``alembic/versions/``.
