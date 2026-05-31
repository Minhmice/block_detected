export type ParamTooltipContent = {
  title: string;
  description: string;
  bullets: string[];
};

export const DETECTION_PARAM_TOOLTIPS: Record<string, ParamTooltipContent> = {
  thresholdMode: {
    title: "Threshold mode",
    description: "Chooses how the frame becomes detection regions.",
    bullets: [
      "Adaptive: best for uneven lighting.",
      "Canny: best for square edge detection.",
      "HSV: useful when block colours are stable.",
      "Wrong setting risk: missed contours or false contours.",
    ],
  },
  blurKernel: {
    title: "Blur kernel",
    description: "Applies blur before edge/threshold detection to reduce noise.",
    bullets: [
      "Increase when: image has grain, tiny dots, or unstable edges.",
      "Decrease when: corners become soft or block borders disappear.",
      "Wrong setting risk: lost block edges or noisy false contours.",
      "Use odd values only: 3, 5, 7.",
    ],
  },
  cannyLow: {
    title: "Canny low threshold",
    description: "Lower edge threshold for Canny detection.",
    bullets: [
      "Increase when: too many weak noise edges appear.",
      "Decrease when: block borders are missed.",
      "Wrong setting risk: false edges or incomplete contours.",
    ],
  },
  cannyHigh: {
    title: "Canny high threshold",
    description: "Upper edge threshold for Canny detection.",
    bullets: [
      "Increase when: background details create extra edges.",
      "Decrease when: block borders are not detected.",
      "Wrong setting risk: incomplete contours or merged noise.",
    ],
  },
  minAreaPx: {
    title: "Minimum area",
    description: "Minimum contour area in pixels.",
    bullets: [
      "Increase when: tiny noise, screws, or dots are detected.",
      "Decrease when: small or far blocks are missed.",
      "Wrong setting risk: valid blocks rejected as too small.",
    ],
  },
  maxAreaPx: {
    title: "Maximum area",
    description: "Maximum contour area in pixels.",
    bullets: [
      "Increase when: close-up blocks are rejected.",
      "Decrease when: huge background regions or merged contours appear.",
      "Wrong setting risk: large valid blocks rejected.",
    ],
  },
  confidenceThresh: {
    title: "Confidence threshold",
    description:
      "Minimum classification confidence before accepting a block.",
    bullets: [
      "Increase when: safer robot pickup is required.",
      "Decrease when: testing and valid blocks are rejected too often.",
      "Wrong setting risk: wrong block commands or missed valid blocks.",
    ],
  },
  resetDefaults: {
    title: "Reset defaults",
    description:
      "Restore recommended detection parameters for a normal 640×480 camera setup.",
    bullets: [
      "Use when: after bad tuning, unstable detection, or failed experiments.",
    ],
  },
} as const;

export const DETECTION_PANEL_FOOTER_TIP =
  "Tip: tune threshold and contour parameters first, then adjust confidence threshold for robot safety.";
