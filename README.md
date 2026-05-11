# Signal Generator

Scientific web application for predicting nanopore resistive pulse signatures, deployed at: [https://tcossalab.net/signalGenerator](https://tcossalab.net/signalGenerator)

## Contributors

See [CONTRIBUTORS.md](./CONTRIBUTORS.md).

## Citation

If you use this tool or reference the underlying model, cite:

Martin Charron, Zachary Roelen, Deekshant Wadhwa, Vincent Tabard-Cossa
**Predicting Resistive Pulse Signatures in Nanopores by Accurately Modeling Access Regions**.  
arXiv:2411.05589 (v2, 2025).  
[https://arxiv.org/abs/2411.05589](https://arxiv.org/abs/2411.05589)

## Project Purpose

This application provides an interactive interface to configure nanopore and analyte geometry, generate predicted resistive pulse signals, and visualize results in the browser. It exists to make the modeling workflow accessible without requiring users to run simulation scripts manually.

The tool is part of the modeling framework presented in the paper above.

## What The Application Currently Supports

Based on current backend and frontend behaviour:

1. Signal generation through a Flask backend endpoint (`generate`).
2. Input validation/sanitization before generation.
3. Support for 2D pore calculations and finite-length pore calculations.
4. Plot-oriented output (`x`, `y`) for visualization.
5. Signal attenuation workflow (`attenuate`) using interpolation, attenuation, and Bessel filtering parameters.
6. Browser-based interaction for component setup, plotting, and result updates.

## Why This README Focuses On Deployment

This repository is maintained by domain scientists, and the app is already publicly deployed. For that reason, this document prioritizes safe update and recovery procedures over local development workflow.

---

## Operational SOP For cPanel Deployment

### 1) Pre-Deployment Backup (Mandatory)

Before any change, create a dated backup copy of:

- `public_html/signalGenerator/static`
- `public_html/signalGenerator/Generator/templates`
- `public_html/signalGenerator/Generator/*.py`

Recommended folder naming: `backup_YYYY-MM-DD`.

### 2) Deploy Static Assets (`static/`) When JS/CSS/Image Files Change

1. Prepare the updated `static` directory.
2. Ensure each `static` subdirectory includes `.htaccess` (required by this deployment setup).
3. Optional helper from repository root:
   - `python staticBundler.py --compress`
4. In cPanel File Manager:
   - Upload `static.zip` to `public_html/signalGenerator`
   - Extract archive
   - Confirm `public_html/signalGenerator/static` was replaced as intended

### 3) Deploy Templates When HTML Structure Changes

Upload updated template file(s) to:

- `public_html/signalGenerator/Generator/templates`

### 4) Deploy Python Backend Files When Logic Changes

Upload updated `.py` files to:

- `public_html/signalGenerator/Generator`

Note: server entry and routing are in `server.py`.

### 5) Restart Application (Mandatory)

After any static, template, or Python change:

1. Open the cPanel Python app page for `tcossalab.net/signalGenerator`.
2. Click **Reset**.
3. Wait for restart completion.

Without reset, updates may not be served.

---

## Post-Deployment Verification

Run this checklist immediately after reset:

1. Open [https://tcossalab.net/signalGenerator](https://tcossalab.net/signalGenerator).
2. Confirm page styling and assets load correctly.
3. Add at least one component and verify that expected input controls appear.
4. Generate a signal and confirm the plot updates successfully.
5. If attenuation settings are used, run attenuation once and confirm the updated output is shown.

## Rollback Procedure

If any deployment introduces errors:

1. Stop further edits on production.
2. Restore backed-up versions of changed files/folders.
3. Reset the cPanel Python app again.
4. Repeat the verification checklist.
5. Record date, files restored, and observed issue for traceability.

---

## Codebase Map (For Future Technical Handover)

- `server.py`: Flask application, routing, and POST handlers.
- `misc.py`: request validation and sanitization helpers.
- `generator_prenormalized.py`: generation path used for 2D pore mode.
- `generator_finitelength_opt.py`: generation path used for finite-length pore mode.
- `sigalModifications.py`: attenuation, interpolation, and filtering utilities.
- `templates/index.html`: primary UI template.
- `static/js/main.js`: frontend entry point and orchestration.
- `static/js/componentInputHandler.js`: component input flow and validation.
- `static/js/componentListHandler.js`: component card/carousel management.
- `static/js/sendAndPlot.js`: generate request/response flow and plotting trigger.
- `static/js/attenuate.js`: attenuation request flow and plotting updates.

## Code Instructions (Expanded)

The JavaScript entry point is `static/js/main.js`. The frontend is modular, and each file has a specific responsibility. For safe maintenance, use the guidance below before editing.

1. `main.js`
   - Initializes common UI behavior (carousel setup, tooltips, dark-mode toggle, resize hooks).
   - Handles shared utility behavior (numeric input guards, random IDs, toasts).
   - Manages molecule YAML import/export helpers and file upload parsing workflow.
   - **When to edit:** global UI behavior, reusable helpers, top-level interactions.

2. `globals.js`
   - Defines global loader object used by multiple modules.
   - Must load before modules that call `loader.show()` / `loader.hide()`.
   - **When to edit:** only for shared global state or app-wide utility bootstrap.

3. `preloader.js`
   - Preloads shape images used in component cards and selector UI.
   - Improves perceived responsiveness by warming image assets on page load.
   - **When to edit:** only when image asset paths or supported shape names change.

4. `componentInputHandler.js`
   - Controls the “Add Component” form lifecycle:
     - clones hidden template forms,
     - sanitizes numeric values,
     - validates geometry against pore constraints,
     - appends validated components to `_ComponentList`.
   - After successful add, it updates:
     - carousel cards,
     - shape plot,
     - internal component list.
   - **When to edit:** component form fields, validation rules, add flow.

5. `componentListHandler.js`
   - Controls card-level actions for existing components:
     - edit (modal),
     - delete,
     - move left/right,
     - duplicate in place / duplicate to end,
     - undo delete (`Ctrl+Shift+Z`).
   - Keeps UI card indices synchronized with `_ComponentList`.
   - Calls `remakeShapesPlotly()` after order/content changes to keep visuals consistent.
   - **When to edit:** carousel behavior and card action logic.

6. `poreLogic.js`
   - Handles pore type selection and pore parameter validation.
   - Supports pore drawing logic for:
     - 2D pore,
     - cylindrical pore,
     - conical pore,
     - hyperbolic pore.
   - Maintains `widthInNanoporeForThingsToPass`, used to validate components against pore geometry.
   - **When to edit:** pore model input rules, pore-specific validation, pore rendering logic.

7. `plotlyShapes.js`
   - Responsible for geometric visualization of components using Plotly shape primitives.
   - Converts component definitions into projected shapes and rebuilds full shape view when needed.
   - Dynamically loads `poreLogic.js` and triggers pore redraw after molecule changes.
   - **When to edit:** projection style, rendering sequence, or shape-plot interaction behavior.

8. `sendAndPlot.js`
   - Validates full model state before sending generation request.
   - Sends POST request with routing parameter `generate` to backend.
   - Plots returned signal (`x`, `y`) and stores both original and attenuated data holders.
   - Provides CSV export and plot utility controls in the Plotly mode bar.
   - **When to edit:** generate request schema, plotting behavior, or result export behavior.

9. `attenuate.js`
   - Handles attenuation parameter input validation and server-side attenuation requests.
   - Sends POST request with routing parameter `attenuate`.
   - Replots attenuated and original traces together for direct comparison.
   - Includes a client-side attenuation helper (`_attenuate`) for local noise simulation logic.
   - **When to edit:** attenuation controls, attenuation plotting behavior, attenuation request payload.

### Practical Editing Rules

- If you change any data field name in forms, update all dependent modules (`componentInputHandler.js`, `sendAndPlot.js`, backend validation in `misc.py`).
- If you change supported shapes or pore types, update image assets, validation logic, and plotting projections together.
- Most card actions and pore edits require a full shape re-render; verify `remakeShapesPlotly()` is still called where needed.
- After frontend edits, always perform a generate flow test and, if applicable, an attenuation flow test before deployment.

## Maintenance Notes

- Prefer small, testable updates over large changes.
- Always keep a recoverable backup before deployment.
- Keep user-facing text clear for lab users and collaborators.
