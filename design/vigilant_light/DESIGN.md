# Design System Specification: Industrial Precision & Architectural Clarity

## 1. Overview & Creative North Star: "The Technical Curator"
This design system moves away from the cluttered, dark-mode aesthetics of traditional ALPR (Automatic License Plate Recognition) interfaces. Our Creative North Star is **The Technical Curator**. 

The goal is to present high-velocity data with the calm, authoritative clarity of a high-end architectural blueprint. We achieve this by rejecting the "template" look—characterized by heavy boxes and dark headers—in favor of a sophisticated high-contrast light theme. We utilize intentional asymmetry, breathable white space, and a rigorous tonal hierarchy to make complex logistical data feel effortless and premium.

## 2. Colors & Surface Philosophy
The palette is rooted in industrial slate and cool grays, punctuated by a high-energy "Alert Orange" to draw the eye to critical data points.

### The "No-Line" Rule
Standard UI relies on 1px borders to separate content. **This design system prohibits 1px solid borders for sectioning.** Boundaries must be defined through:
*   **Background Shifts:** Distinguish a sidebar from a content area using a shift from `surface` (#f5fafa) to `surface-container-low` (#f0f5f4).
*   **Tonal Transitions:** Use a slightly darker `surface-variant` to anchor a footer without drawing a line.

### Surface Hierarchy & Nesting
Treat the dashboard as a series of physical layers. We use the surface-container tiers to create "nested" depth:
1.  **Canvas (Base):** `surface` (#f5fafa).
2.  **Structural Sections:** `surface-container-low` (#f0f5f4) for large layout blocks.
3.  **Active Widgets/Cards:** `surface-container-lowest` (#ffffff) to provide a "lifted" feel against the darker canvas.
4.  **Interactive Overlays:** `surface-container-highest` (#dee3e3) for hover states or active selection.

### The "Glass & Gradient" Rule
To escape a "flat" corporate feel, use **Glassmorphism** for floating elements (e.g., license plate zoom-ins or filter popovers). Apply a backdrop-blur of 12px-20px with a 70% opacity `surface-container-lowest`. 
*   **Signature Textures:** Use subtle linear gradients for primary CTAs, transitioning from `primary` (#0f1f29) to `primary_container` (#25343f) at a 135-degree angle. This adds a "metallic" soul to the tech-heavy interface.

## 3. Typography: The Editorial Scale
We use **Inter** exclusively. It is a typeface designed for screens, and we leverage its variable weights to create a clear information scent.

*   **Display & Headlines:** Use `display-md` or `headline-lg` for macro-metrics (e.g., total vehicle counts). Tighten the tracking (letter-spacing) by -0.02em for a "custom" editorial feel.
*   **Title & Body:** `title-md` is for card headers. `body-md` is the workhorse for plate data and timestamps.
*   **Technical Labels:** Use `label-sm` in All Caps with +0.05em tracking for metadata (e.g., "REGION CODE," "CONFIDENCE SCORE"). This mimics industrial labeling systems.
*   **The Hierarchy Goal:** Use size and weight—not just color—to signify importance. High-contrast navy (`primary`) on a crisp light background ensures the eye finds the plate number first.

## 4. Elevation & Depth: Tonal Layering
Depth is achieved through "Tonal Stacking" rather than traditional drop shadows.

*   **The Layering Principle:** Place a `surface-container-lowest` card on top of a `surface-container-low` background. The subtle delta in brightness creates a natural, soft lift.
*   **Ambient Shadows:** For floating elements like modals, use an extra-diffused shadow: `box-shadow: 0 20px 40px rgba(15, 31, 41, 0.06);`. Note the use of the `on-surface` navy color for the shadow tint, ensuring it looks like natural ambient light.
*   **The "Ghost Border" Fallback:** If a border is required for accessibility, it must be a **Ghost Border**: Use the `outline-variant` (#c3c7cb) at 20% opacity. Avoid 100% opaque borders at all costs.

## 5. Components & Interaction Patterns

### Buttons
*   **Primary:** A deep navy `primary` to `primary_container` gradient. High-contrast white text. `md` (0.375rem) roundedness.
*   **Secondary:** `surface-container-highest` background with `on-surface` text. No border.
*   **Tertiary (Alert):** Use `tertiary_fixed_dim` (#ffb786) for primary actions that require caution.

### Data Chips (The ALPR Signature)
*   **License Plate Chip:** A `surface-container-lowest` chip with a Ghost Border. Use `title-md` for the plate string to ensure maximum legibility.
*   **Status Chips:** Use `tertiary_container` (Orange/Brown) for "Flagged" vehicles and `secondary_container` for "Authorized."

### Input Fields
*   Instead of a box, use a `surface-container-low` background with a 2px bottom-weighted line using `primary` only when the field is focused. This maintains the "Industrial-Tech" minimalism.

### Cards & Data Lists
*   **Forbid Divider Lines:** Separate list items using a 12px vertical gap or by alternating background tones between `surface-container-low` and `surface-container-lowest`.
*   **The "Plate Zoom" Component:** Use Glassmorphism for the overlay that appears when hovering over a cropped vehicle image.

## 6. Do's and Don'ts

### Do:
*   **Do** prioritize vertical rhythm. Use 8px grid increments for all spacing.
*   **Do** use the Vibrant Orange (`tertiary`) sparingly. It is a "signal" color—if it's everywhere, it's nowhere.
*   **Do** leverage asymmetry. A metric card can be larger than the list next to it to create visual interest.

### Don't:
*   **Don't** use pure black (#000000). Always use the `on-surface` navy for text.
*   **Don't** use standard "Material Design" shadows. Keep them diffused and barely visible.
*   **Don't** use 1px solid lines for layout division. Let the background tones do the work.
*   **Don't** crowd the interface. If a screen feels "busy," increase the `surface` padding rather than adding lines.