# Rebuild the Running Route Generator

## Summary

- Convert the project into a conventional single-command Flask app: Flask serves the page, static assets, and API from one origin.
- Generate true road-following loop routes from OpenStreetMap data, measured from actual edge lengths and accepted only within ±5% of the requested 1–20 km distance.
- Use Gemini as a bounded two-step agent: choose among deterministic route candidates, then turn structured street segments into concise runner directions. A deterministic local fallback always works without Gemini.

## Implementation Changes

- Restructure into a Flask entry point with `templates/index.html`, `static/app.js`, and `static/styles.css`; serve `/` and replace the hard-coded `127.0.0.1:5002` frontend request with a same-origin API request.
- Add dependency/configuration files and update the README with one startup command, environment-variable setup, API-key safety guidance, and removal of obsolete experimental scripts.
- Replace the random walk with deterministic candidate-loop generation over OSMnx’s walk network:
  - Generate multiple circular/via-point loop candidates around the start node.
  - Measure final edge lengths, reject candidates outside ±5%, and score remaining candidates by distance accuracy first and repeated-edge length second.
  - Return a clear “no suitable loop” response when none exists rather than silently returning an inaccurate route.
- Build the displayed polyline from OSM edge geometries—not only node coordinates—so curved roads render along their real mapped shapes.
- Produce structured route segments from graph edges: merge consecutive segments on the same named road, prefer available OSM name/ref metadata, and replace unnamed fragments with concise “continue” instructions rather than repeatedly exposing “unnamed street.”
- Define `POST /api/routes` with `{ postcode, distance_km }` input and a response containing GeoJSON route geometry, requested/actual distance, distance error, local turn steps, AI-enhanced directions, and whether AI or fallback directions were used.
- Migrate Gemini usage to the supported Python SDK. Keep the key server-side and make AI optional:
  - Call 1: Flash-Lite selection agent may inspect only a capped catalogue of candidate summaries through read-only tools and choose a valid candidate.
  - Call 2: Flash-Lite directions agent receives only the chosen, merged route segments and returns concise sidebar text.
  - Cap calls at two per Generate click, cap response tokens, enforce timeouts, disable automatic retries, and fall back to locally generated directions on missing key, quota, invalid output, or API failure.
  - Make model name and AI enablement environment-configurable. Gemini API billing/quota is managed through the API project, so monitor it in AI Studio rather than relying on the consumer subscription. [Google Gemini API billing](https://ai.google.dev/gemini-api/docs/billing)

## UI and Error Handling

- Keep Leaflet as the map renderer; add a responsive sidebar showing actual distance, target tolerance status, concise directions, and a notice when local fallback directions are shown.
- Show loading, validation, geocoding, no-loop-found, map-data, and server errors clearly; prevent duplicate submissions while a request is active.
- Keep UK-postcode validation explicit and reject distances outside 1–20 km before network or AI calls.

## Test Plan

- Unit-test input validation, route-distance calculation, ±5% candidate acceptance/rejection, repeated-road scoring, geometry expansion, and named/unnamed segment merging.
- Mock OSMnx and Gemini to test agent selection, malformed AI output, no API key, quota/API failure, and deterministic fallback.
- Add Flask endpoint tests for `/`, successful route responses, invalid postcode/distance, and no feasible loop.
- Manually verify a known postcode such as `BN6 8LP`: the polyline follows bends in streets, actual distance is within tolerance, and directions are short and mostly named-road based.

## Assumptions

- Version one supports UK postcodes and 1–20 km requests only.
- A valid loop is preferred; out-and-back routes are not returned automatically.
- When several loops meet tolerance, the app prefers minimal road repetition.
- No AI request is made beyond the two capped calls initiated by a user click; route generation remains usable without Gemini.
