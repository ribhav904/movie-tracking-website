# Frontend Product and Design Plan

## Product objective

Create a personal entertainment archive that makes discovery, logging, reflection, and ranking
feel like one coherent product. The interface must handle movies, television, games, and books
without making any category feel secondary. It should be fast enough for daily logging and calm
enough for long-form browsing.

The frontend talks directly to Supabase only for email/password authentication and session
refresh. Every application-data request uses the FastAPI `/api/v1` contract.

## Design philosophy: the quiet archive

The product should feel like a carefully maintained personal collection rather than a streaming
service, social network, or generic analytics dashboard.

Principles:

1. **Content before chrome.** Artwork, titles, dates, ratings, and personal context are the visual
   hierarchy. Navigation supports them without competing for attention.
2. **Editorial structure.** Strong typography, deliberate whitespace, thin rules, and measured
   alignment create character. Panels are used only when they clarify containment.
3. **One meaningful accent.** A muted moss accent communicates selection and action. Statuses use
   a small, consistent semantic palette.
4. **Data with context.** A number is always paired with a label, period, source, or comparison.
   The interface avoids decorative metrics.
5. **Progressive disclosure.** Everyday actions remain close at hand while advanced metadata and
   administration stay secondary.
6. **Honest states.** Loading, empty, error, stale-provider, provisional-rating, and offline states
   explain what is happening and what the user can do next.

Explicit visual constraints:

- No gradients.
- No emoji.
- No glassmorphism, glowing borders, floating blobs, or ornamental charts.
- No excessive pills, oversized rounded cards, or generic icon grids.
- No fake AI language, fabricated recommendations, or vague motivational copy.
- No animation that delays a task; motion is limited to 140–180 ms state transitions.

## Visual system

### Color

Light mode uses a warm paper canvas, near-white surfaces, charcoal text, stone borders, and a
muted moss accent. Dark mode uses near-black olive-neutral surfaces rather than pure black.

Both themes are token-based and meet WCAG AA contrast for text and interactive controls. The
theme defaults to the operating-system preference, can be explicitly changed, and persists on the
device.

### Typography

- Geist Sans for interface and editorial text.
- Geist Mono for dates, compact statistics, progress values, and rating provenance.
- Headings use weight and spacing rather than novelty typefaces.
- Body copy stays between 15 and 17 pixels with comfortable line height.

### Shape and spacing

- Four-pixel base spacing grid.
- Small 6–10 pixel radii for controls and panels; media artwork keeps its natural rectangular
  character.
- One-pixel borders are preferred over shadows. Shadows are reserved for temporary overlays.
- Minimum 44-pixel touch targets and visible keyboard focus rings.

## Information architecture

### Primary navigation

- Today: recent activity, current media, quick logging, and a year-at-a-glance strip.
- Discover: provider-backed exploration and search across all four media types.
- Library: saved media with status, type, rating, favorite, tag, and sort controls.
- Activity: chronological consumption history and logging entry points.
- Reports: yearly contribution calendar, totals, category mix, streaks, and rating distribution.
- Battle Arena: focused pair comparison and type-specific Elo rankings.
- Recommendations: explainable suggestions based on the existing catalog and personal history.

Account, appearance, export, and owner administration sit in a secondary settings surface.

### Responsive behavior

- Desktop: fixed compact sidebar and a centered content canvas.
- Tablet: reduced sidebar and two-column content where useful.
- Mobile: compact top bar, bottom navigation for the most-used destinations, single-column cards,
  and full-width action sheets.

## Core flows

### Authentication

1. User signs in with email and password through Supabase Auth.
2. Session is restored and refreshed by the Supabase client.
3. Access token is attached to FastAPI requests.
4. Unknown or inactive memberships return a clear access message and sign-out action.

Public signup is intentionally absent.

### Discovery and import

1. Choose or search a media type.
2. Review normalized provider results with public-rating provenance.
3. Open a detail view.
4. Import the item and add it to the library with an initial status.

### Consumption logging

1. Open a library item or use the global Log activity action.
2. Start or continue a cycle.
3. Record progress, duration, episode, date, and optional notes.
4. Complete the cycle when appropriate.

The local activity date is always visible and editable independently from the exact timestamp.

### Battle Arena

1. Choose a media category.
2. Compare two completed items in a distraction-free split layout.
3. Select left, right, or tie exactly once.
4. Move immediately to the next unplayed pair.
5. View Elo, Battle Score, rank, match record, and provisional status separately from manual and
   public ratings.

## Frontend architecture

- React 19 and TypeScript using the Vinext App Router starter.
- Server-rendered route shells with client components only where interaction or browser state is
  required.
- TanStack Query for FastAPI server state, caching, retries, mutation state, and invalidation.
- Supabase JavaScript client for Auth only.
- Zod for environment and form-boundary validation.
- Recharts for accessible report charts; the contribution calendar is semantic HTML/CSS.
- Lucide for a restrained, consistent icon set.
- `date-fns` for date formatting and calendar construction.
- Hand-authored CSS design tokens and components; no UI kit and no utility-class dependency in
  product components.

Directory intent:

```text
frontend/
├── app/                 Route entry points and metadata
├── components/          Reusable product and layout components
├── features/            Domain-specific UI and queries
├── lib/                 API, Auth, query, dates, and utility code
├── providers/           Theme, session, and query providers
├── styles/              Tokens and component-level styles
├── tests/               Render and behavioral tests
└── public/              Static product assets only
```

## Data and state rules

- FastAPI remains the source of truth for catalog, library, activity, reports, Arena, and
  administration.
- Query keys are domain-based and include all filtering inputs.
- Mutations provide an `Idempotency-Key` where the backend accepts one.
- Provider failures distinguish fresh, stale cached, empty, and unavailable states.
- Theme and optional layout density are the only local-storage preferences.
- No application records are duplicated into browser storage.

## Accessibility and quality requirements

- WCAG 2.2 AA contrast and keyboard navigation.
- Semantic landmarks, real buttons and links, labelled forms, and useful document titles.
- Focus is restored when dialogs close and moves to validation summaries on failed submission.
- Reduced-motion preferences are respected.
- Charts have text summaries and do not communicate meaning by color alone.
- Empty and error states retain a clear next action.
- Layout works from 360 pixels through large desktop widths.

## Delivery sequence

1. Establish the token system, typography, theme persistence, responsive shell, and base
   components.
2. Add Supabase session handling, guarded routes, and the authenticated FastAPI client.
3. Build Today, Discover, Library, and shared media components.
4. Build Activity logging, Reports, Battle Arena, Recommendations, and Settings.
5. Add loading, empty, stale, error, and permission states.
6. Validate formatting, lint, TypeScript, tests, production output, accessibility, and responsive
   behavior.
7. Deliver through the repository issue, feature branch, pull request, and CI workflow.

## Initial release acceptance criteria

- All planned routes render and share one coherent responsive shell.
- Light and dark themes work without gradients and persist correctly.
- A valid Supabase session can call protected FastAPI endpoints.
- The user can browse/search media, view and update the library, inspect activity and reports,
  complete Arena comparisons, and review recommendations.
- Missing environment configuration produces a useful setup screen rather than a crash.
- Lint, TypeScript, automated tests, and the production build pass.
