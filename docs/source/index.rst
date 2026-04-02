ooai-promptdb
=============

A prompt registry and runtime delivery layer for LangChain and LangGraph.

Version, alias, and deliver prompts through a relational database (Postgres or
SQLite), export bundles to blob storage (local filesystem or MinIO), and access
everything through a Python client, FastAPI API, Rich CLI, or Streamlit
dashboard.

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Quickstart
      :link: quickstart
      :link-type: doc

      Install, initialize a workspace, and register your first prompt in under
      a minute.

   .. grid-item-card:: Python Client
      :link: client-guide
      :link-type: doc

      Register, resolve, render, and export prompts from Python code.

   .. grid-item-card:: Prompt Files
      :link: prompt-files
      :link-type: doc

      Author prompts as YAML, JSON, or plain text files and register them
      directly.

   .. grid-item-card:: CLI Reference
      :link: cli
      :link-type: doc

      ``promptdb init``, ``list``, ``register-file``, ``resolve``, ``render``,
      and ``export-file``.

   .. grid-item-card:: HTTP API
      :link: http-api
      :link-type: doc

      FastAPI endpoints for registration, resolution, rendering, and export.

   .. grid-item-card:: Architecture
      :link: architecture
      :link-type: doc

      Layered design, persistence model, and resolution order.

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   quickstart
   client-guide
   prompt-files
   cli
   http-api
   architecture

.. toctree::
   :maxdepth: 2
   :caption: Development
   :hidden:

   testing
   publishing
   workflows

.. toctree::
   :maxdepth: 2
   :caption: Reference
   :hidden:

   api
