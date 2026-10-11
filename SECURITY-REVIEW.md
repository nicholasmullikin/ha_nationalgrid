# National Grid security review — 2026-10-11

Scope: ha_nationalgrid at a3dc45bdc260a69ebfc37ff3e7d6f8e534a02dba and
py-nationalgrid 0.6.6 at 554e4b93ec07a87caa2de4487d43d6705081490a.
Static review covers the runtime modules and pinned dependency wheel; no claim
is made about the security of National Grid's servers or all transitive packages.

## Confirmed findings and remediation

- **Medium: diagnostic identifier disclosure.** `selected_accounts` was not in
  the redaction set, and meter keys contained account/service-point identifiers.
  Redact selections and substitute anonymous `meter_N` keys. Synthetic regression
  tests check serialized diagnostics, including keys.
- **Medium: sensitive logs.** The integration logged raw exceptions and account
  or meter IDs. The dependency logged authentication redirect locations (which
  can include authorization codes), API error payloads, request URLs and exception
  tracebacks. Replace these with operation summaries, counts, error classes and
  HTTP statuses at all log levels. GraphQL response exceptions use a fixed message
  instead of embedding backend payloads. Do not dump data objects in support requests.
- **Low: credential repr disclosure.** NationalGridConfig's generated repr
  included username/password, custom headers and the API subscription key.
  Exclude these fields from repr. Exception string summaries omit response data,
  URLs, queries and nested exceptions; private context attributes are retained.

## Reviewed behavior and remaining risks

HTTPS verification defaults to enabled. The integration does not disable it.
OIDC uses PKCE; ID-token verification checks signature, issuer, audience and time.
Access-token subject extraction intentionally skips signature verification on a
token received over verified TLS and does not make an authorization decision.
No dynamic code execution, shell commands or unrelated outbound endpoints were
found in the runtime source reviewed. This is not a proof that code is safe.

The custom component runs inside Home Assistant and shares its filesystem,
credentials and host-network access. Account passwords are retained in HA's
config-entry storage, not encrypted by this integration. Protect `.storage`,
secrets and private backups; use an SSH tunnel for credential-bearing setup.
The dependency's detailed context attributes and generic HA/SQL debug logs can
still expose IDs if deliberately dumped. Keep global debug logging disabled.
Account IDs remain in private device/statistics IDs so Energy sources are stable.

Startup includes an idempotent SQL migration for the old National Grid domain.
Its queries are fixed rather than interpolated user input, but they can replace
conflicting statistics. Initial imports and force-refresh can consume RAM, disk,
API quota and recorder time. Back up first, verify no old integration conflicts,
monitor the initial import and do not expose refresh actions to Assist/MCP.
National Grid may only return partial history; absent data is not zero usage.

## Portal compatibility

On 2026-10-11 the public consumer portal used a different OAuth client and
policy from upstream's hard-coded UWP policy. That policy returned a B2C
exception before credential validation. The fork now matches the public
portal's OAuth parameters, tenant path, transaction query parameters, normal
sign-in form choice and SelfAsserted confirmation endpoint. Form requests stay
on the verified issuer host. The business portal settings remain unchanged.
Request-shape and destination regression tests cover this change. OAuth now
uses HTTPX with verified TLS and scoped cookie transfer to the aiohttp caller.
Regression tests verify domain/path/Secure scope across redirects and private
transport errors. API data requests remain on aiohttp. The saved login succeeded
in both the browser and corrected library, confirming two active billing accounts.
Account setup and Energy imports require separate live verification.

## Packaging and tests

The dependency fork release is 0.6.6.post4; its wheel is pinned by URL and SHA-256
in manifest.json. The integration fork release is 0.0.0.post5. Update deliberately
from reviewed commits; never deploy a moving branch as a version pin.

Dependency suite: 231 passed, 99.80% coverage (OIDC helper excluded by upstream
coverage configuration; privacy tests explicitly exercise its logging).
Integration suite: 284 passed, 100% measured coverage, including recorder overlap
regressions, login/re-auth flows, diagnostics and synthetic secret logging tests.
The full suites ran on Python 3.14.7 with HA test runtime 2026.10.1; deployment
checks additionally target the live HA 2026.9.4 container. Ruff checks pass.
