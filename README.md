# User Management REST API

[![CI](https://github.com/wasofy/user-management-api/actions/workflows/ci.yml/badge.svg)](https://github.com/wasofy/user-management-api/actions/workflows/ci.yml)
[![CodeQL](https://github.com/wasofy/user-management-api/actions/workflows/codeql.yml/badge.svg)](https://github.com/wasofy/user-management-api/actions/workflows/codeql.yml)

A Spring Boot CRUD API for managing users, packaged and operated the way a
production service would be: containerised, tested in CI on every push, and
security-scanned at the source, dependency and image level.

## Tech stack

- Java 17, Spring Boot 4.1, Spring Data JPA, Bean Validation
- PostgreSQL 16 (Docker), H2 (tests and local dev)
- Docker multi-stage build, Docker Compose
- GitHub Actions CI, Python smoke test
- CodeQL, Trivy, Dependabot

## Quickstart

Requires Docker. One command, working API:

```bash
cp .env.example .env   # set your own credentials
docker compose up -d
curl http://localhost:8080/actuator/health
```

## API

Base path: `/api/users`

| Method | Path              | Description        | Success | Errors |
|--------|-------------------|--------------------|---------|--------|
| GET    | `/api/users`      | List all users     | 200     |        |
| GET    | `/api/users/{id}` | Get one user       | 200     | 404    |
| POST   | `/api/users`      | Create a user      | 201     | 400, 409 |
| PUT    | `/api/users/{id}` | Update a user      | 200     | 400, 404, 409 |
| DELETE | `/api/users/{id}` | Delete a user      | 204     | 404    |

Requests carry a plain `password` field which is hashed server-side with
BCrypt. Responses never contain the hash: the response DTO has no password
field at all. Duplicate emails return 409, validation failures return 400
with per-field messages.

## Architecture

Controller, service and repository layers with DTOs at the API boundary:

- `UserController` handles HTTP concerns only: routing, status codes,
  the Location header on create.
- `UserService` owns business logic, transactions, password hashing and the
  DTO-to-entity mapping. The JPA entity never leaves this layer.
- `UserRepository` is a Spring Data `JpaRepository`.
- `GlobalExceptionHandler` maps exceptions to JSON error responses
  (404, 400 with field errors, 409 on constraint violations) without leaking
  schema details.

The application runs in three modes, selected by Spring profiles with no code
changes: in-memory H2 for tests, file-based H2 for local development, and
PostgreSQL via the `docker` profile in containers.

## Container setup

The Dockerfile is a multi-stage build: Maven and the JDK exist only in the
build stage, the runtime image is a slim Alpine JRE with the JAR. The process
runs as a non-root user and a `HEALTHCHECK` probes `/actuator/health`, which
is the only Actuator endpoint exposed.

Docker Compose runs the app together with PostgreSQL. The database publishes
no host port, credentials come from an untracked `.env` file, the app waits
for a passing `pg_isready` healthcheck before starting, and data lives in a
named volume.

## CI pipeline

Every push and pull request to `main` runs three jobs:

1. **build-and-test** - Maven build and the full test suite (JDK 17, cached
   dependencies)
2. **docker-smoke-test** - builds the image, starts the full compose stack
   and runs `scripts/smoke_test.py` against it: waits for health, then
   exercises the complete CRUD cycle plus the 400/404/409 error paths,
   failing the pipeline on the first wrong response
3. **image-scan** - Trivy scans the built image and fails the pipeline on
   fixable critical or high CVEs

## Security

Secure SDLC layering, each scanner covering a different surface:

- **CodeQL** (SAST) analyses the Java source for vulnerability patterns on
  every push and on a weekly schedule.
- **Trivy** scans the container image, covering OS packages and the
  dependencies inside the JAR. The pipeline fails on fixable critical or
  high findings.
- **Dependabot** raises weekly update PRs for Maven dependencies and the
  GitHub Actions themselves.

Application-level measures: BCrypt password hashing, DTOs that make hash
exposure impossible by construction, generic error messages that do not leak
schema internals, a non-root container user, a single exposed Actuator
endpoint, and no credentials anywhere in the repository.

## Running tests

```bash
./mvnw test                      # unit and API tests on in-memory H2
python scripts/smoke_test.py     # end-to-end against a running instance
```
