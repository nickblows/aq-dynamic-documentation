# AQIE-Citizen-Alpha

> The original 2023 alpha prototype of the citizen-facing air quality service, built as a Java
> Spring Boot application. Retained for historical reference only.

## 1. Service Metadata

| Field | Value |
|---|---|
| Repository | [`DEFRA/AQIE-Citizen-Alpha`](https://github.com/DEFRA/AQIE-Citizen-Alpha) |
| Service domain | `Citizen` |
| Service type | `Prototype Service (including PoC)` |
| Lifecycle stage | `Archived` |
| Primary language | Java (catalogued as CSS by GitHub language detection) |
| Runtime | Java 20 (Spring Boot, Maven) |
| Default branch | `main` |
| Created (UTC) | `2023-07-21` |
| Last main commit (UTC) | `2023-07-31T15:25:36Z` |
| Last analysed commit | `f7fbb115` |
| Last analysed (UTC) | `2026-09-15T00:00:00Z` |
| Activity status | `Archived` |

## 2. Purpose and Responsibilities

> **Archived.** The alpha prototype for the AQIE citizen service. Superseded in beta by
> `aqie-front-end` (Node.js / Hapi / GOV.UK Frontend) and the `aqie-back-end` data API.
> Retained for historical reference. Do not deploy.

**Does:**

- Demonstrates the core citizen journey trialled in alpha: find monitoring sites near a
  postcode, view pollutant measurements, and view the highest recent measurements.
- Trials three mapping approaches side by side — Google Maps, Ordnance Survey raster tiles
  and Ordnance Survey vector tiles — to inform the beta mapping decision.
- Renders server-side HTML with Thymeleaf and no JavaScript framework, deliberately following
  the GDS progressive enhancement guidance.

**Does not:**

- Ingest data from Ricardo, the Met Office or any live upstream provider. Site and measurement
  data is loaded from a small committed SQL seed file into H2 or PostgreSQL.
- Represent the current architecture. Nothing in this repository is carried forward in code;
  only the journey design informed the beta.

**Lineage.** The README states plainly that this is "the alpha prototype for our Citizen
service". The journeys it prototypes (postcode search, nearest monitoring sites, pollutant
measurements, mapping) are the journeys delivered in beta by `aqie-front-end`, and the OS Names
and postcode lookups it trials are now performed by `aqie-location-backend` and
`aqie-back-end` respectively. The succession is clear in intent, but there is no shared code
and no repository record of a formal handover.

## 3. Architecture

- **Pattern:** Spring Boot MVC monolith. Controllers that return a rendered view are prefixed
  `Display`; the remaining controllers expose a small JSON REST API. Data access uses
  `JdbcTemplate` with hand-written SQL and a repository implementation per database engine.

| Component | Path | Responsibility |
|---|---|---|
| Display controllers | `src/main/java/.../endpoint/Display*.java` | Render Thymeleaf views for sites, measurements and maps |
| REST controllers | `src/main/java/.../endpoint/{AirQuality,Site,Measurement}Controller.java` | JSON API over the same domain objects |
| Mapping proxies | `src/main/java/.../endpoint/OS*MappingController.java` | Proxy OS raster and vector tile requests so the API key is not exposed to the browser |
| Repositories | `src/main/java/.../repository/` | H2 and PostgreSQL implementations selected by profile |
| Views | `src/main/resources/templates/` | Thymeleaf templates using a locally copied GOV.UK stylesheet |
| Seed data | `src/main/resources/data.sql` | A handful of monitoring sites, used with the H2 profile |

## 4. API Surface

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/greeting` | Landing page used during development |
| `GET` | `/sites`, `/nearestSites` | List all sites; form for nearest-site search |
| `POST` | `/nearestSites` | Nearest monitoring sites for a submitted postcode |
| `GET` \| `POST` | `/measurements`, `/highest_measurements` | Measurement search forms and results |
| `GET` | `/google_mapping`, `/os_raster_mapping`, `/os_vector_mapping` | The three mapping spikes |
| `GET` | `/proxy_os_raster_mapping`, `/proxy_os_vector_mapping/**` | Server-side tile proxy |
| `GET` | `/api/aq`, `/api/sites`, `/api/measurements` (and `/{id}` variants) | JSON REST API over the seeded data |

## 5. Consumes (Outbound Dependencies)

| Target | Type | Endpoint / Mechanism | Data exchanged | Auth |
|---|---|---|---|---|
| postcodes.io | External API | `GET https://api.postcodes.io/postcodes/{postcode}` | Postcode in; coordinates out | None |
| Ordnance Survey Maps API | External API | Raster WMTS and vector tile endpoints, via the in-app proxy | Map tiles and styles | `OS_MAPPING_KEY` |
| Google Maps | External API | Browser-side map embed | Map tiles | Key supplied at runtime |
| H2 or PostgreSQL | Datastore | JDBC, selected by Spring profile | Seeded sites, pollutants and measurements | Local development credentials |
| unpkg / polyfill.io CDNs | External | Browser-side script includes | MapLibre GL and polyfills | None |

No AQIE service is called. This prototype predates the AQIE service estate.

## 6. Consumed By (Inbound Dependencies)

None. Nothing has ever depended on this repository.

> Edges are mastered in [`/docs/integration-catalog.yaml`](../../../integration-catalog.yaml).

## 7. Data

- **Stores:** H2 in-memory (default alpha profile) or a local PostgreSQL container.
- **Key entities:** `Site`, `Pollutant`, `Measurement`, `AirQuality`, `LocationPoint`.
- **Retention / refresh:** none. Data is inserted from `data.sql` at start-up under the H2
  profile and is lost on restart. The seeded rows are a small sample of public AURN site
  metadata; no personal data is present.

## 8. Configuration

Variable and property **names** only.

| Variable / property | Purpose |
|---|---|
| `spring.profiles.active` | Selects `localwithh2`, `localwithpostgre` or `localdockerwithpostgre` |
| `OS_MAPPING_KEY` / `os.mapping.key` | Ordnance Survey Maps API key, injected at runtime |
| `spring.datasource.url`, `.username`, `.password` | JDBC connection for the selected profile |
| `spring.data.rest.base-path` | Root path for the Spring Data REST API |

> **Security note.** Local development database passwords for the H2 and PostgreSQL profiles
> are committed as literal values in the `application-*.properties` files. They are
> throwaway local credentials and are not used by any deployed environment, but they are
> present in a public repository and should be removed or replaced with placeholders if the
> repository is retained. The Ordnance Survey key is correctly a runtime placeholder.

## 9. Hosting and Deployment

- **Platform:** none. Never deployed to CDP.
- **Container:** a hand-written `Dockerfile` on `openjdk:20-jdk` running the built jar, plus a
  helper image for local PostgreSQL under `docker/postgresImage/`.
- **Environments:** local only.
- **Pipelines:** none. There are no GitHub Actions workflows.

## 10. Observability

- **Logging:** Logback, configured in `logback-spring.xml`.
- **Tracing / metrics:** none.

## 11. Open Questions

- [ ] Confirm with the service owner that `aqie-front-end` is the formal successor. The
      relationship is evident from the README and journey design but is not recorded anywhere.
- [ ] Is there an alpha assessment report or service design record that should be linked from
      here? That, rather than the code, is the lasting value of this repository.
- [ ] The repository is already archived on GitHub. Agree whether to delete it, or to keep it
      and strip the committed local database passwords first.
- [ ] Which mapping approach did the alpha spike recommend, and does the current
      `aqie-maps-frontend` follow that recommendation?
