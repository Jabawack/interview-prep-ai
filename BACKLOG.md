# InterviewPrepAI — Backlog

## Done
- [x] FastAPI backend with SSE streaming
- [x] LangGraph pipeline (intent parser → parallel agents → response composer)
- [x] Job search agent + tools (jobspy integration)
- [x] Company research agent + tools (DB-backed)
- [x] Chat streaming endpoint (`/api/v1/chat/stream`)
- [x] CRUD endpoints for jobs, companies, conversations
- [x] Next.js frontend with chat UI
- [x] SSE streaming hook + parser
- [x] Agent step visualization (ReAct cycles, parallel agents)
- [x] Database migrations (4 files)
- [x] Tests (intent parser, pipeline, job tools, company tools)
- [x] README, .gitignore, .env.example

## In Progress
- [ ] Backend local setup (venv, deps, env config)
- [ ] Neon project creation + run migrations

## Backlog — MVP
- [ ] Seed company profiles data (company research returns empty without it)
- [ ] Conversation persistence (save/load chat history to DB)
- [ ] Interview prep agent (intent routed but agent not built)
- [ ] Salary research agent (intent routed but agent not built)

## Backlog — Post-MVP
- [ ] Authentication (Neon Auth or NextAuth)
- [ ] Rate limiting on chat endpoint
- [ ] Company data web scraping tool (instead of relying on seeded DB)
- [ ] Jobs/companies/conversations UI pages (endpoints exist, no frontend yet)
- [ ] Conversation history sidebar
- [ ] Message editing/deletion
- [ ] Deploy (Vercel frontend, Railway/Fly backend)
- [ ] CI/CD pipeline
- [ ] Input autocomplete/hints
