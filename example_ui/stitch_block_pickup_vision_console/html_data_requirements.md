# Robo-Vision OS v2.4 - HTML Data & State Requirements

This document outlines all the dynamic data fields, interactive inputs, and telemetry points present in the `code.html` frontend layout. It serves as a mapping guide for connecting the HTML UI to the underlying Python backend logic.

## 1. Top Navigation & Global Actions
These elements control the high-level state of the system and engine.

* **NEXT CAMERA (Button)**: Cycles through available physical/virtual camera inputs.
* **NEXT MODEL (Button)**: Cycles through available AI/YOLO models.
* **START / STOP (Toggle Button)**: Controls the main inference/rendering engine loop.

## 2. Viewport Header Toolbar
Contains rendering toggles and real-time performance metrics.

* **Overlay Toggles (Checkboxes)**:
  * `Contours`: Enable/disable contour drawing.
  * `Corners`: Enable/disable corner drawing.
  * `Warped Face`: Enable/disable warped face rendering.
* **Performance Metrics**:
  * `FPS`: Float value (e.g., `59.8`).
  * `Latency`: Integer/Float value in milliseconds (e.g., `12ms`).
  * `Render Time`: Float value in milliseconds (e.g., `1.8ms`).

## 3. Main Camera Feed
* **Image Stream**: The `<img>` `src` attribute needs to be updated continuously with the base64 encoded frame or a streaming URL (e.g., MJPEG stream).

## 4. Bottom Telemetry Panel
Read-only data emitted by the vision pipeline for the primary target.

### 4.1 Primary Detect
* **Object Class**: String (e.g., `BLOCK_01`).
* **Confidence**: Float/Percentage (e.g., `98.4%`).
* **Confidence Bar Chart**: Width CSS property (`width: 98.4%`).

### 4.2 Kinematics
* **Target Status**: String (e.g., `acquired`, `tracking`, `lost`).
* **Center (px)**: Array/Tuple of two integers `[X, Y]` (e.g., `[640, 480]`).
* **Angle (deg)**: Float (e.g., `45.2°`).
* **Pose (mm)**: Float (e.g., `-12.5`).

### 4.3 System Log
* **Log Entries**: List of messages containing:
  * `Timestamp` (e.g., `[14:32:01.005]`)
  * `Message` (e.g., `Model loaded successfully.`)
  * `Level/Type` (to determine CSS color formatting: error, primary, secondary, text-on-surface-variant).

## 5. Right Sidebar (Vision Pipeline Configuration)
Inputs that adjust the OpenCV/YOLO inference parameters. The backend needs to listen to changes on these fields and apply them to the runtime engine.

### 5.1 Pre-Processing
* **Contrast**: Float (Range: `0.0` - `2.0`, Step: `0.1`, Default: `1.2`).
* **Brightness**: Integer (Range: `-100` - `100`, Step: `1`, Default: `10`).
* **Saturation**: Float (Range: `0.0` - `3.0`, Step: `0.1`, Default: `1.0`).

### 5.2 Inference
* **Confidence**: Float (Range: `0.0` - `1.0`, Step: `0.01`, Default: `0.13`).
* **NMS IoU**: Float (Range: `0.0` - `1.0`, Step: `0.01`, Default: `0.45`).

### 5.3 Stability
* **Blur Kernel**: Odd Integer (Min: `1`, Step: `2`, Default: `5`).
* **Min Area (px²)**: Integer (Step: `10`, Default: `150`).
* **Temporal Smoothing**: Boolean (Checkbox).

### 5.4 Edge Detection
* **Canny Low**: Integer (Range: `0` - `255`, Default: `50`).
* **Canny High**: Integer (Range: `0` - `255`, Default: `150`).

### 5.5 ROI Selection
* **X**: Integer (Default: `0`).
* **Y**: Integer (Default: `0`).
* **WIDTH**: Integer (Default: `1280`).
* **HEIGHT**: Integer (Default: `720`).

## 6. Pinned Footer Actions
* **Configuration Profile Selection (Dropdown)**: String value (e.g., `default`, `high_contrast`, `low_light`).
* **SAVE CONFIG (Button)**: Persists current parameters to the selected profile.
* **DELETE (Button)**: Deletes the selected configuration profile.
