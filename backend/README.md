# Repo Visualizer Backend

A professional FastAPI backend for analyzing a code repository, extracting file metadata, detecting dependencies, computing code metrics, building a dependency graph, and generating AI-powered explanations for files.

## What this backend does

This backend takes a repository path and performs the following pipeline:

1. Scans the repository recursively
2. Ignores junk folders like `.git`, `node_modules`, `__pycache__`, `dist`, `build`, `.venv`
3. Detects file language and file metadata
4. Extracts dependencies
   - Python: `ast` based import extraction
   - C++: `#include` parsing
5. Computes metrics
   - LOC
   - blank lines
   - comment lines
   - code lines
   - complexity score
6. Builds graph JSON
   - nodes
   - edges
   - graph statistics
7. Optionally generates AI summaries for files
8. Caches analysis and summaries for repeated runs

---

## Backend architecture

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── analyze.py
│   │   ├── graph.py
│   │   └── health.py
│   ├── core/
│   │   ├── config.py
│   │   ├── cache.py
│   │   └── constants.py
│   ├── models/
│   │   ├── file_model.py
│   │   ├── graph_model.py
│   │   └── metrics_model.py
│   ├── services/
│   │   ├── scanner.py
│   │   ├── graph_builder.py
│   │   ├── metrics.py
│   │   └── ai_summary.py
│   ├── parsers/
│   │   ├── base.py
│   │   ├── python_parser.py
│   │   └── cpp_parser.py
│   └── utils/
│       ├── hashing.py
│       └── file_utils.py
├── tests/
├── requirements.txt
└── README.md