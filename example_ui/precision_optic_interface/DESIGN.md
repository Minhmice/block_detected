---
name: Precision Optic Interface
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#bcc9cd'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#869397'
  outline-variant: '#3d494c'
  surface-tint: '#4cd7f6'
  primary: '#4cd7f6'
  on-primary: '#003640'
  primary-container: '#06b6d4'
  on-primary-container: '#00424f'
  inverse-primary: '#00687a'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffb2b7'
  on-tertiary: '#67001b'
  tertiary-container: '#ff7f8b'
  on-tertiary-container: '#7d0023'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#acedff'
  primary-fixed-dim: '#4cd7f6'
  on-primary-fixed: '#001f26'
  on-primary-fixed-variant: '#004e5c'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdadb'
  tertiary-fixed-dim: '#ffb2b7'
  on-tertiary-fixed: '#40000d'
  on-tertiary-fixed-variant: '#92002a'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  data-lg:
    fontFamily: JetBrains Mono
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  data-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 16px
  margin: 24px
  container-padding: 12px
---

## Brand & Style
The design system is engineered for high-stakes robotic environments where split-second data interpretation is critical. The brand personality is **clinical, authoritative, and high-fidelity**, mirroring the precision of the hardware it controls. 

The aesthetic follows a **Modern Engineering Console** style:
- **High Information Density:** Maximum utility per pixel, reducing the need for scrolling.
- **Instrumental Aesthetics:** UI elements resemble physical lab equipment with clear state indications.
- **Visual Silence:** A "Dark Mode First" approach to minimize eye strain in low-light laboratory settings, using subtle borders instead of heavy shadows to define structure.
- **Technical Precision:** Use of monospaced fonts for all telemetry to ensure numerical alignment and rapid scanning.

## Colors
This design system utilizes a "Slate & Zinc" foundation to create a non-distracting backdrop for colorful data overlays.

- **Primary (Cyan-500):** Used for active states, selection focus, and primary action buttons.
- **Success (Emerald-500):** Reserved exclusively for "System Connected," "Block Identified," and "Optimal Path" statuses.
- **Danger (Rose-500):** Strictly for "Emergency Stop," "Vision Failure," or "Collision Imminent" alerts.
- **Warning (Amber-500):** Used for "Low Light," "Degraded Accuracy," or "Hardware Heat" warnings.
- **Neutral/Surface:** A range of deep slates provides the structural layers. Backgrounds use the darkest values, while containers use slightly lighter tones to indicate elevation without shadows.

## Typography
The typographic system is split between **Inter** for structural UI (navigation, headings, settings) and **JetBrains Mono** for all dynamic data.

- **Legibility:** JetBrains Mono ensures that numerical data (coordinates, confidence scores, timestamps) remains perfectly aligned in tabular layouts.
- **Hierarchy:** Use `label-caps` for all form labels and metadata headers to distinguish them from the data they describe.
- **Density:** Tight line heights are preferred to keep information compact on engineering consoles.

## Layout & Spacing
The layout follows a **Fixed Dashboard Grid** optimized for 1080p and 4K laboratory monitors. 

- **Grid System:** A 12-column grid. The camera preview usually occupies an 8-column span, with a 4-column "Telemetry Sidebar" for real-time logs and controls.
- **Modular Panels:** Each functional area (Camera, Arm Controls, Object List) is housed in a distinct panel with a 1px border.
- **Spacing Rhythm:** Based on a 4px baseline. Use 16px (4 units) for standard gaps between modules and 8px for internal padding within modules to maintain high density.
- **Mobile Consideration:** On smaller displays, the sidebar collapses into a bottom drawer, prioritizing the camera feed.

## Elevation & Depth
In this design system, depth is communicated through **Tonal Layering and Borders** rather than shadows, which can appear muddy on high-brightness industrial screens.

- **Level 0 (Background):** Slate-950 (#020617) - The base canvas.
- **Level 1 (Panels):** Slate-900 (#0f172a) - The standard container for controls.
- **Level 2 (Inlays):** Slate-800 (#1e293b) - Used for input fields, code blocks, and nested list items.
- **Borders:** All interactive elements and containers must have a 1px solid border (#334155). Active elements increase border brightness to the primary accent color.

## Shapes
The shape language is **Soft (0.25rem)** to provide a modern feel while retaining an industrial, "machined" look.

- **Standard Elements:** Buttons, inputs, and panels use 4px (0.25rem) rounding.
- **Large Components:** Camera previews and main dashboard cards use 8px (0.5rem) rounding.
- **Data Tags:** Status indicators and chips use 2px rounding to maintain a sharp, technical profile.

## Components
### Buttons & Switches
- **Primary Action:** Solid Slate-100 with Slate-900 text. Use for "Initialize."
- **Status Switches:** Laboratory-style toggle switches with a visible "well" background. The "on" state should glow subtly with the primary color.
- **Emergency Stop:** A large, high-contrast Rose-600 button with white text, always fixed in the top-right or bottom-right corner.

### Data Readouts
- **Value Displays:** Use a combination of a small `label-caps` header and a large `data-lg` value.
- **Trend Indicators:** Small sparklines (simplified line charts) embedded next to numerical values to show stability over time.

### Camera Preview Container
- **Overlays:** Use a 2px Emerald stroke for detected "Block" bounding boxes.
- **Crosshairs:** A fixed cyan crosshair in the center of the feed with X/Y coordinate readouts in the corner using `data-md`.

### Sliders
- **Technical Sliders:** Thin tracks (2px) with rectangular "machined" handles. Provide numerical input fields adjacent to all sliders for precise manual override.

### Input Fields
- **Monospace Inputs:** All coordinate and threshold inputs must use monospaced fonts and high-contrast focus rings to prevent data entry errors.