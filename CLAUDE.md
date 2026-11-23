# Agentic SDLC Capstone Project

## Objective
Implement a complete 8-stage Agentic SDLC pipeline using Claude Code:
1. Requirements Analysis
2. Architecture Design
3. Design Review
4. Implementation Planning
5. Development
6. Code Review
7. Verification
8. GitHub Pull Request

## Application
Build a Task Management REST API with FastAPI, SQLAlchemy, SQLite, Pydantic v2, and Pytest.
Keep changes focused on the Jira story requirements without adding unnecessary microservices, cloud setup, or extra frameworks.

## Workflow & Artifacts
- Orchestrator entry point: .claude/commands/run-sdlc-workflow.md
- Specialized agents: .claude/agents/
- State tracking: context/workflow-context.json
- SDLC deliverables: docs/plans/

## Human Approval Checkpoints
Require explicit user confirmation before proceeding past:
- Requirements Analysis
- Implementation Planning
- Final PR Review

Do not fabricate test executions, approvals, or tool outputs. Never expose secrets.
