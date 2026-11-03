# Interface direction

AgentGate is a spending review tool. Its visual hierarchy should help an owner read the proposed carts, available funds, and payment evidence before acting.

- **Typography:** self-hosted Public Sans, licensed under the SIL Open Font License. Body copy starts at 16px; labels and secondary evidence remain at least 13–14px. Numbers use tabular figures.
- **Palette:** forest `#123d33` for navigation, teal `#086b59` for primary actions, ink `#142c24` on pale neutral `#f2f6f3`. Approval uses amber; failures use dark red with a text label. Status never depends on color alone.
- **Layout:** generous card padding, visible section boundaries, full navigation labels on mobile, and a single-column review at narrow widths. Long identifiers wrap rather than push the page wider.
- **Interaction:** visible keyboard focus, readable native form controls, and at least 44px primary targets. Approval and payment actions retain explicit labels.

The video uses the same interface and typeface. A visible pointer, click rings, and event-timed camera moves identify the actual action and its result. Camera moves return to the wider interface between sections.
