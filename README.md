# Repo Visualizer with AI Insights

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=000" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-0052CC?logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Vite-6.x-646CFF?logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Gemini-AI-7B61FF?logo=google&logoColor=white" alt="Gemini" />
</p>

<p align="center">
  <b>An AI-powered repository analysis tool that helps you understand codebases faster.</b><br/>
  Scan a local project, inspect its dependency graph, read file-level summaries, and see repository-wide insights in one place.
</p>

---

## Table of Contents

- [Overview](#overview)
- [Why I built this](#why-i-built-this)
- [What it can do](#what-it-can-do)
- [Screenshots](#screenshots)
- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Tech stack](#tech-stack)
- [Setup](#setup)
- [Environment variables](#environment-variables)
- [Running locally](#running-locally)
- [API endpoints](#api-endpoints)
- [Repository intelligence](#repository-intelligence)
- [Complexity heatmap](#complexity-heatmap)
- [Search and filters](#search-and-filters)
- [AI features](#ai-features)
- [Folder layout](#folder-layout)
- [Design choices](#design-choices)
- [Limitations](#limitations)
- [Future improvements](#future-improvements)
- [What I learned](#what-i-learned)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Repo Visualizer is a full-stack project that makes unfamiliar repositories easier to understand.

Instead of opening files one by one and trying to piece everything together manually, the app gives you a visual map of the codebase, basic software metrics, and AI-generated explanations for important files and architecture patterns.

The project combines three things:

- static analysis
- interactive visualization
- AI-assisted explanation

That combination makes it useful for onboarding, code review, debugging, and general repository exploration.

---

## Why I built this

When you first open a new codebase, it is easy to get lost.

You usually need to figure out:

- which files matter most
- how the project is structured
- where the dependencies are
- which modules are central
- what should be read first
- how complex the codebase feels overall

That takes time.

This project was built to reduce that time by turning the repository into something that is easier to browse and easier to explain.

My goal was not just to show files on a graph, but to make the codebase feel more approachable.

---

## What it can do

When you analyze a repository, the app:

- scans supported source files
- skips hidden, temporary, and binary files
- detects file languages
- calculates repository metrics
- builds a dependency graph
- shows complexity visually
- generates a summary for individual files
- generates a summary for the overall architecture
- generates repository intelligence with health, recommendations, and hotspots
- caches AI outputs so repeated analysis is faster

The result is a dashboard that gives both a high-level and a detailed view of the project.

---

## Screenshots

Add your screenshots here once you capture them.

### Suggested images

- dashboard overview
- dependency graph
- search and filters
- file summary
- architecture summary
- repository intelligence
- repository copilot / AI chat

### Example layout

```md
![Dashboard](docs/screenshots/dashboard.png)
![Graph](docs/screenshots/graph.png)
![Search](docs/screenshots/search.png)
![File Summary](docs/screenshots/file-summary.png)
![Architecture Summary](docs/screenshots/architecture-summary.png)
![Repository Intelligence](docs/screenshots/repository-intelligence.png)
```

---

## How it works

The overall flow looks like this:

```text
Repository path
      │
      ▼
Repository scanner
      │
      ├──► file metadata
      ├──► dependency map
      ├──► metrics
      └──► graph data
                  │
                  ▼
         Frontend dashboard
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
   Graph      AI summaries   Repository intelligence
```

### Backend flow

1. The user enters a repository path.
2. The backend scans the project.
3. The scanner collects supported files and metadata.
4. Parsers extract imports and relationships.
5. Metrics are calculated.
6. Graph nodes and edges are built.
7. AI services generate summaries.
8. Results are cached for reuse.

### Frontend flow

1. The user runs analysis from the dashboard.
2. The graph and stats appear.
3. The user can search, filter, and inspect nodes.
4. Clicking a node loads the file summary.
5. Architecture and repository intelligence panels provide higher-level context.

---

## Project structure

```text
backend/
└── app/
    ├── api/
    ├── core/
    ├── models/
    ├── parsers/
    ├── services/
    ├── utils/
    ├── main.py
    └── schemas.py

frontend/
└── src/
    ├── api/
    ├── assets/
    ├── components/
    ├── types/
    ├── utils/
    ├── App.tsx
    └── App.css
```

---

## Tech stack

### Frontend

- React
- TypeScript
- Vite
- React Flow
- React Markdown

### Backend

- FastAPI
- Python
- Pydantic

### AI

- Google Gemini

### Utilities

- pathlib
- ast
- hashlib
- json
- dotenv

---

## Setup

### Prerequisites

Make sure you have:

- Python 3.13 or compatible Python 3.x
- Node.js 18+ or 20+
- npm
- a Gemini API key

### Clone the repository

```bash
git clone <your-repository-url>
cd repo-visualizer
```

### Backend installation

```bash
cd backend
pip install -r requirements.txt
```

### Frontend installation

```bash
cd frontend
npm install
```

---

## Environment variables

Create a `.env` file inside the backend folder.

```env
GEMINI_API_KEY=your_api_key_here
CACHE_DIR=.cache
DEBUG=false
CORS_ORIGINS=*
MAX_FILE_SIZE_BYTES=1048576
```

### What they do

- `GEMINI_API_KEY` enables AI features
- `CACHE_DIR` stores cached analysis outputs
- `DEBUG` toggles FastAPI debug mode
- `CORS_ORIGINS` controls which frontend origins can access the API
- `MAX_FILE_SIZE_BYTES` sets the size limit for scanned files

---

## Running locally

### Start the backend

```bash
cd backend
py -3.13 -m uvicorn app.main:app --reload
```

### Start the frontend

```bash
cd frontend
npm run dev
```

Open the local Vite URL shown in the terminal.

---

## API endpoints

### Health

```http
GET /health
```

Checks whether the backend is available.

### Analyze repository

```http
POST /analyze
```

Scans the repository and returns metrics, graph data, and dependency information.

### File summary

```http
POST /summary/file
```

Returns an AI summary for a selected file.

### Architecture summary

```http
POST /summary/architecture
```

Returns an AI summary of the repository structure.

### Repository intelligence

```http
POST /repository-ai
```

Returns repository health, recommendations, and hotspots.

### Repository chat

```http
POST /repository-chat
```

Lets you ask questions about the repository.

---

## Repository intelligence

This section gives the repository a more “at a glance” view.

It includes:

- health score
- maintainability
- architecture quality
- complexity level
- recommendations
- hotspots

This is useful when you want to quickly understand whether a repository looks clean, modular, or likely to need attention.

---

## Complexity heatmap

The graph uses two signals:

- node background color = folder or module group
- node border color = complexity

### Border colors

- green = low complexity
- yellow = moderate complexity
- orange = high complexity
- red = critical complexity

That makes it easier to spot files that may need a deeper look.

---

## Search and filters

The graph can be filtered by:

- file name
- file path
- language
- module group

This helps when the repository gets large and the graph starts to feel crowded.

There is also a reset option so the whole view can be cleared quickly.

---

## AI features

The app uses Gemini in three places:

### 1. File summary
Explains what a file does, what functions/classes matter, and what the file is responsible for.

### 2. Architecture summary
Explains the repository layout, main modules, hotspots, and refactoring suggestions.

### 3. Repository intelligence
Gives a score and highlights possible improvements.

### 4. Repository chat
Lets you ask questions like:

- Where should I start reading this repository?
- Which file is most important?
- Which module is most complex?
- What should I refactor first?

---

## Folder layout

### Backend

- `app/api` — route handlers
- `app/core` — config and cache helpers
- `app/models` — Pydantic models
- `app/parsers` — Python/C++ parsing helpers
- `app/services` — scanning, metrics, graph, and AI logic
- `app/utils` — file and hashing utilities

### Frontend

- `src/api` — frontend API client
- `src/components` — reusable UI parts
- `src/types` — shared TypeScript types
- `src/utils` — layout helpers
- `src/App.tsx` — main dashboard
- `src/App.css` — styling

---

## Design choices

A few choices shaped this project:

### Why FastAPI?
It keeps the backend clean, typed, and easy to extend.

### Why React Flow?
It is a good fit for interactive dependency graphs and node-based exploration.

### Why caching?
AI calls can be slow and expensive, so caching makes repeated analysis much smoother.

### Why separate services?
The backend is easier to maintain when scanning, metrics, graph construction, and AI generation are split into small services.

### Why markdown rendering?
AI answers are much easier to read when headings and lists render properly.

---

## Limitations

No project is perfect, and this one still has a few limitations:

- dependency resolution is strongest for the languages supported by the parsers
- very large repositories can still take time to scan
- AI output may vary depending on the repository context
- some unusual project structures may need extra parsing logic
- the graph can get busy if the repository is large

These are normal tradeoffs for a tool like this.



---

 
## Final note

The goal of this project is simple:

> help someone understand a repository faster.

That is the main idea behind the graph, the metrics, and the AI features.

It started as a visualizer, but it became much more useful once the explanations and repository insights were added.

---
## 🎬 Demo

The animation below demonstrates the complete repository analysis workflow, including backend integration, repository scanning, dependency visualization, architecture insights, repository metrics, and AI-powered code analysis.

<p align="center">
  <img src="docs/demo.gif" alt="Repo Visualizer Demo" width="1000"/>
</p>