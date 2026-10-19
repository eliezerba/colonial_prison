# v8.2 — regression, typography and language audit

## Compatibility with v7
Automated structural comparison found 7/7 original views and no missing DOM element ID in v8.2 relative to v7. All 43 baseline chart containers remain; additional panels and interactive graphics are governed by the unchanged app.js visualisation handlers. The 34 inherited automated tests pass after a complete rebuild of 2,248 observations, 50 sources and 43 jurisdictions.

## Typography
The main hero heading was reduced from a maximum of 31px to 25px, the site brand from 18px to 15px, card headings from 16px to 15px and descriptive visual hierarchy was adjusted at tablet and mobile widths. Plot heights have not been reduced.

## Language
A persistent Hebrew/English toggle was added to the top bar. It changes document direction and translates major navigation, controls, chart headings and user guidance through a curated glossary. Source and archival names, raw data, provenance, Plotly-generated legend and axis text, and some dynamically generated analytical detail remain in their original language. **The English translation is not a complete localization of every dynamic result.** That remains a separate work item if fully English analytical commentary is required.

## GitHub Pages
The deployment workflow publishes the `site/` directory on main/master. Its rebuild preserves `site/assets/language.js`, the lab SVG, and the edited stylesheet and HTML template. Upload the *contents* of the project folder to the root of your repository.

## Verification scope
Structural checks, JS syntax checks and inherited unit tests passed. A new, comprehensive browser screenshot/regression run was not completed in this pass; correct rendering at deployed GitHub Pages should be confirmed with live acceptance testing.
