# Readability revision validation

The November 3, 2026 revision replaces the small IBM Plex text and blue-grey palette with self-hosted Public Sans, a 16px body baseline, forest navigation, high-contrast teal actions, and clearer approval and failure states. See [DESIGN.md](DESIGN.md) for the visual direction.

Checks completed against the running app:

- Production Next.js build passed.
- All six main views checked at widths 1440, 1024, 768, 390 and 360px: no page-wide horizontal overflow. Wide data tables retain their own horizontal scrolling.
- A computed text/background contrast check examined 1,253 text-bearing elements across the six desktop views. No checked pair fell below 4.5:1 for normal text or 3:1 for large text. This covers the rendered text and solid backgrounds sampled by the check, rather than a full accessibility certification.
- Desktop and phone screenshots reviewed for hierarchy, navigation, long payment identifiers and readable form controls.
- The isolated judge workflow passed: authenticated demo entry, foreign-origin rejection, owner approval, two simulated payments, receipt replay, phone layouts and reset. No browser page errors were observed.
- The real sandbox mission remains captured at $100 spent and $0 reserved. Filming-only reservations were released without creating additional payment orders.

The revised recording uses the actual interface at 1440×720. It includes a visible pointer and click pulses, with smooth event-timed camera moves. The edited app area is 1800×900 within the 1080p video; captions occupy a separate band below the interface.
