# aqie-prtr-submissions-frontend

> A frontend scaffold for the Pollutant Release and Transfer Register (PRTR) submissions service. It is
> the CDP Node.js frontend template plus English and Welsh language support. The About page says the
> service lets you submit your pollutant release and transfer data, but nothing can be submitted yet.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/aqie-prtr-submissions-frontend`](https://github.com/DEFRA/aqie-prtr-submissions-frontend) |
| Service domain | `Citizen` |
| Service type | `Auxilary Frontend` |
| Lifecycle stage | `Prototype/PoC` |
| Primary language | JavaScript |
| Runtime | Node.js `>=24` (ES modules), pinned to `v24.22.1` in `.nvmrc` |
| Default branch | `main` |
| Created (UTC) | `2026-10-23` |
| Last main commit (UTC) | `2026-11-09T14:28:41Z` |
| Last analysed commit | `b6e229d7` |
| Last analysed (UTC) | `2026-11-19T00:00:00Z` |
| Activity status | `Active` |

## 2. Purpose and Responsibilities

**Intended:** the public-facing side of a PRTR submissions service, where users would submit their
pollutant release and transfer data. The repository does not say who the users are. The only statement of
purpose is one sentence on the About page: "This service lets you submit your pollutant release and
transfer data."

**Actual:** the CDP Node.js frontend template with a home page that has a title and no content, an About
page with that one sentence and a "What you can do" heading with nothing beneath it, and the template's
cookie preferences page. The only service-specific work is bilingual support, written between 26 and 29
October 2026 and merged to `main` on 9 November.

**Does:**

- Serves a GOV.UK-styled shell: header, service navigation (Home and About), footer, breadcrumbs and
  error pages.
- Offers English (`en-GB`) and Welsh (`cy`). The language comes from the `?language=` query parameter, is
  remembered in the server-side session and defaults to English. The switch link is shown only when at least
  one Welsh string exists, which is the case today. Only the home title and the About page are translated.
  The navigation labels, cookie banner, cookies page, footer and error pages are English only.
- Runs the standard cookie consent flow. Analytics cookies are off until the visitor opts in, and the server
  removes Google cookies when they decline. Google Tag Manager loads only after consent and only if a
  container key is configured (the repository sets none).
- Protects form posts with CSRF tokens, sets a content security policy and marks rendered pages
  `no-store`.

**Does not:**

- Accept or submit any data. There is no form, file upload or sign-in anywhere in the service.
- Call any backend. There is no backend URL setting and no HTTP client, so it is not connected to
  `aqie-prtr-submissions-backend`, `aqie-prtr-backend` or any other AQIE service.
- Use the CDP Uploader, GOV.UK Notify, an identity or sign-in provider, S3 or SQS.
- Show any register data. Searching and downloading the published register is `aqie-prtr-frontend`.

**Relationship to the existing PRTR services.** It shares the `aqie-prtr-` name with `aqie-prtr-frontend`,
`aqie-prtr-backend` and `aqie-prtr-submissions-backend`, but none of those repositories refers to it, and it
links to none of them. The shared name is the only link. It does not replace the public register, which is
a separate read-only journey. On `main` it stands alone. See Section 11.

## 3. Architecture

**Pattern:** CDP Node.js frontend template. A Hapi server-side rendered GOV.UK Frontend service using
Nunjucks, with `yar` sessions on a Catbox cache and Vite-built assets. Route folders hold a registration
module, a controller, optional `content.js` copy in English and Welsh, and a `.njk` template.

| Component | Path | Responsibility |
|---|---|---|
| Server | `src/server/server.js` | Builds the Hapi server, security headers and session cache; registers the plugins; installs the error handler |
| Router | `src/server/plugins/router.js` | Registers the health, cookies, home and about routes and the static asset handling |
| Home | `src/server/routes/home/` | `GET /`, title only |
| About | `src/server/routes/about/` | `GET /about`, the one-sentence description |
| Cookies | `src/server/routes/cookies/` | Cookie preferences page and the post that saves the choice |
| Health | `src/server/routes/health/` | `GET /health` |
| Language selection | `src/server/plugins/language-selection.js`, `src/server/common/helpers/i18n.js` | Chooses the language and builds the message catalogue from each route's `content.js` and `src/server/common/content.js` |
| Cookie consent | `src/server/plugins/cookie-consent.js`, `src/server/common/helpers/cookie-policy-manager.js`, `src/client/javascripts/cookies.js` | Consent cookie, banner state, server-side removal of Google cookies, client-side enhancement |
| CSRF | `src/server/plugins/csrf.js` | `@hapi/crumb` token on form posts |
| Content security policy | `src/server/plugins/content-security-policy.js` | `blankie` policy with nonces, allowing the Google analytics hosts |
| Session cache | `src/server/plugins/session-cache.js`, `src/server/common/helpers/session-cache/cache-engine.js`, `src/server/common/helpers/redis-client.js` | `yar` sessions on `catbox-redis` or `catbox-memory` |
| Static assets | `src/server/plugins/serve-static-files.js`, `src/client/`, `vite.config.js` | Vite-built assets served under `/public` |
| Templating | `src/config/nunjucks/`, `src/server/common/templates/` | Nunjucks environment, GOV.UK layout, header, service navigation and footer |
| Error handling | `src/server/common/helpers/errors.js` | Renders an error page for client and server errors |
| Config | `src/config/config.js` | `convict` schema with strict validation |

## 4. API Surface

Routes are user-facing HTML pages unless noted.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness probe (JSON `{ message: 'success' }`) |
| `GET` | `/` | Home page (title only) |
| `GET` | `/about` | About the service |
| `GET` | `/cookies` | Cookie preferences, with an optional `updated` flag |
| `POST` | `/cookies` | Saves the analytics choice (`analytics`, `async`, `returnUrl`, CSRF token); JSON reply when `async`, otherwise a redirect to a same-site return address or `/cookies?updated=true` |
| `GET` | `/favicon.ico`, `/public/{param*}` | Static assets |

Any page accepts `?language=en-GB` or `?language=cy`. Unsupported values are ignored. There are no
authenticated routes.

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| Redis | Datastore | `catbox-redis` over `ioredis` (`REDIS_HOST`); in-memory cache outside production | Server-side session cache holding the language preference | `REDIS_USERNAME`, `REDIS_PASSWORD`, TLS in production |
| Google Tag Manager / Google Analytics | External (browser-side) | Script loaded by the visitor's browser from `googletagmanager.com` | Page view events | Container ID in `GOOGLE_TAG_MANAGER_KEY` |

The Google edge is dormant: nothing loads unless `GOOGLE_TAG_MANAGER_KEY` is set and the visitor has accepted
analytics cookies. The link to the GOV.UK privacy and accessibility pages in the footer is a static
hyperlink, not a runtime call. There are no calls to any AQIE service.

## 6. Consumed By (Inbound Dependencies)

| Consumer | Endpoint used | Data exchanged |
|---|---|---|
| Public internet (visitors) | All HTML routes above | Language and cookie choices in; pages out |
| CDP platform | `GET /health` | Liveness check |

No AQIE service calls this one, and a GitHub code search of the DEFRA organisation, including the PRTR
journey and performance test suites, finds no other public repository that names it.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml). The only edge
> is the dormant browser-side analytics edge. The catalogue records the absence of a link to
> `aqie-prtr-submissions-backend` and to the existing PRTR pair under `refuted_edges`.

## 7. Data

- **Stores:** none of its own. Redis is used only as a server-side session cache (`catbox-redis`, `@hapi/yar`),
  falling back to in-memory locally. The default key prefix is the service name.
- **Session keys held:** `language` only. The CSRF token is held in a cookie, not in the session.
- **Cookies set:** the session cookie, the CSRF cookie and a consent cookie
  (`aqie-prtr-submissions-frontend_policy`) recording essential and analytics choices. No personal data
  is persisted.
- **Retention:** the session cache and session cookie both last four hours by default
  (`SESSION_CACHE_TTL`, `SESSION_COOKIE_TTL`); the consent cookie lasts one year; static assets are cached
  for one week.
- MongoDB and Floci appear in `compose.yml` only, inherited from the template, and are not used.

## 8. Configuration

Variable names only. Values are held in CDP secrets and never recorded here.

| Variable | Purpose |
|---|---|
| `PORT`, `HOST` | HTTP listener |
| `NODE_ENV`, `SERVICE_VERSION` | Runtime identity |
| `ASSET_PATH`, `STATIC_CACHE_TIMEOUT` | Static asset serving |
| `REDIS_HOST`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_KEY_PREFIX`, `REDIS_TLS`, `USE_SINGLE_INSTANCE_CACHE` | Session cache backend |
| `SESSION_CACHE_ENGINE`, `SESSION_CACHE_NAME`, `SESSION_CACHE_TTL` | Catbox cache selection and lifetime |
| `SESSION_COOKIE_PASSWORD`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_TTL` | Session cookie signing and lifetime. The password has a committed placeholder default, so confirm the variable is set in CDP |
| `GOOGLE_TAG_MANAGER_KEY` | Google Tag Manager container ID; analytics are inactive while it is empty |
| `TRACING_HEADER` | CDP trace header name |
| `LOG_ENABLED`, `LOG_LEVEL`, `LOG_FORMAT`, `LOG_REDACT` | Logging |
| `HTTP_PROXY`, `ENABLE_SECURE_CONTEXT` | Declared in config but not read by service code |
| `NODE_USE_ENV_PROXY`, `HTTPS_PROXY`, `NO_PROXY` | Platform outbound proxy. The README says the platform sets them; service code does not read them |

## 9. Hosting and Deployment

- **Platform:** DEFRA Core Delivery Platform (CDP) on AWS ECS. The repository is the CDP Node.js frontend
  template and publishes through the CDP build action.
- **Container:** multi-stage build from `defradigital/node-development` through a `production_build` stage
  to `defradigital/node`, parent image `3.2.4-node24.22.1`, with `TZ` set to `Europe/London` and `curl` added
  for the platform health check. `prestart` and the image build run the Vite frontend build. Entrypoint
  `node src`.
- **Environments:** the repository does not show which CDP environments host the service.
- **Local development:** `compose.yml` provides Redis, MongoDB (unused) and a Floci AWS emulator, with the
  service container still named `your-frontend` and a commented-out backend example.
- **Pipelines:**
  - `.github/workflows/check-pull-request.yml` runs the security audit, `npm ci`, the Vite build, format
    check, lint, tests and a Docker build test, and the Sonar scan when `SONAR_TOKEN` is set.
  - `.github/workflows/publish.yml` tests, builds and publishes through the CDP build action on push to
    `main`, then runs Sonar without failing the build.
  - `.github/workflows/publish-hotfix.yml` is a manual hotfix publish.
- **Testing:** `vitest` with coverage and `cheerio` for rendered-markup assertions.

## 10. Observability

- **Logging:** `pino` through `hapi-pino`, ECS format in production, with `LOG_REDACT` paths applied. In
  production the `authorization` and `cookie` request headers and all response headers are removed. `/health` is
  excluded from request logs.
- **Tracing:** `@defra/hapi-tracing` using `TRACING_HEADER`.
- **Metrics:** `@defra/cdp-metrics`.
- **Auditing:** `@defra/cdp-auditing` is declared but never imported, so no audit events are emitted.
- **Security headers:** `blankie` with `@hapi/scooter` for the content security policy, Hapi HSTS, no-sniff
  and frame protection, and `Cache-Control: no-store` on rendered pages.
- **Shutdown:** `hapi-pulse`.

## 11. Open Questions

- [ ] (catalogue `oq-032`) What is the intended relationship between this service and the existing register? Nothing links the
      two, so it is unknown whether submissions will reach `aqie-prtr-backend`, feed its TSV or XML route, or
      stay separate.
- [ ] (catalogue `oq-032`) Who will submit data (operators, regulators or both), and how will they sign in? There is no
      authentication or form on `main`.
- [ ] (catalogue `oq-032`) Will this frontend call `aqie-prtr-submissions-backend`? There is no backend URL setting yet.
- [ ] (catalogue `oq-032`) Is the service deployed to any CDP environment, and when is a first release expected? The
      repository does not say.
- [ ] Welsh: is a full translation a requirement? Only the home title and About page are translated today.
- [ ] Before accepting data: service-specific privacy, cookies and accessibility pages (the footer links to
      the generic GOV.UK pages), a data protection assessment, audit events and confirmation that
      `SESSION_COOKIE_PASSWORD` is set in CDP.
- [ ] Which analytics container, if any, will `GOOGLE_TAG_MANAGER_KEY` hold, and under which analytics
      tenant?
