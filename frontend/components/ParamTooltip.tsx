"use client";

import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

import type { ParamTooltipContent } from "@/lib/detectionParamTooltips";

export type { ParamTooltipContent };

const TOOLTIP_WIDTH = 340;
const TOOLTIP_MAX_WIDTH = 380;
const TOOLTIP_MIN_WIDTH = 320;
const TOOLTIP_MAX_HEIGHT = 220;
const VIEWPORT_PADDING = 8;
const GAP = 8;

type ArrowPlacement = "top" | "bottom";

type TooltipPosition = {
  top: number;
  left: number;
  arrowPlacement: ArrowPlacement;
  arrowOffset: number;
};

function computePosition(
  anchor: DOMRect,
  tooltipWidth: number,
  tooltipHeight: number,
): TooltipPosition {
  const pad = VIEWPORT_PADDING;
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const anchorCenterX = anchor.left + anchor.width / 2;

  let left = anchor.left + anchor.width / 2 - tooltipWidth / 2;
  let top = anchor.bottom + GAP;
  let arrowPlacement: ArrowPlacement = "top";

  if (left + tooltipWidth > vw - pad) {
    left = vw - pad - tooltipWidth;
  }
  if (left < pad) {
    left = pad;
  }

  if (anchor.right > vw - pad - 48 && left + tooltipWidth > vw - pad) {
    left = Math.max(pad, anchor.right - tooltipWidth);
  }

  if (top + tooltipHeight > vh - pad) {
    top = anchor.top - tooltipHeight - GAP;
    arrowPlacement = "bottom";
  }

  if (top < pad) {
    top = anchor.bottom + GAP;
    arrowPlacement = "top";
  }

  const arrowOffset = Math.min(
    Math.max(anchorCenterX - left - 6, 14),
    tooltipWidth - 14,
  );

  return { top, left, arrowPlacement, arrowOffset };
}

function TooltipBody({ content }: { content: ParamTooltipContent }) {
  return (
    <div className="normal-case tracking-normal">
      <p className="mb-1.5 font-mono text-[13px] font-semibold leading-[1.4] text-on-surface">
        {content.title}
      </p>
      <p className="font-mono text-xs leading-[1.4] text-on-surface/90">
        {content.description}
      </p>
      <ul className="mt-2 space-y-1.5 font-mono text-xs leading-[1.4] text-on-surface/85">
        {content.bullets.map((bullet) => (
          <li key={bullet} className="flex gap-2">
            <span aria-hidden className="shrink-0 text-primary/70">
              •
            </span>
            <span>{bullet}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ParamTooltip({ content }: { content: ParamTooltipContent }) {
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [position, setPosition] = useState<TooltipPosition | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const tooltipId = useId();

  const visible = open || pinned;

  useEffect(() => {
    setMounted(true);
  }, []);

  const updatePosition = useCallback(() => {
    const trigger = triggerRef.current;
    const panel = panelRef.current;
    if (!trigger || !panel) return;

    const anchor = trigger.getBoundingClientRect();
    const tooltipWidth = Math.min(
      TOOLTIP_MAX_WIDTH,
      Math.max(TOOLTIP_MIN_WIDTH, panel.offsetWidth || TOOLTIP_WIDTH),
    );
    const tooltipHeight = Math.min(panel.offsetHeight, TOOLTIP_MAX_HEIGHT);

    setPosition(computePosition(anchor, tooltipWidth, tooltipHeight));
  }, []);

  useLayoutEffect(() => {
    if (!visible) {
      setPosition(null);
      return;
    }
    updatePosition();
  }, [visible, content, updatePosition]);

  useEffect(() => {
    if (!visible) return;

    function handleReposition() {
      updatePosition();
    }

    window.addEventListener("resize", handleReposition);
    window.addEventListener("scroll", handleReposition, true);
    return () => {
      window.removeEventListener("resize", handleReposition);
      window.removeEventListener("scroll", handleReposition, true);
    };
  }, [visible, updatePosition]);

  useEffect(() => {
    if (!pinned) return;
    function handlePointerDown(event: MouseEvent | TouchEvent) {
      const target = event.target as Node;
      if (
        triggerRef.current?.contains(target) ||
        panelRef.current?.contains(target)
      ) {
        return;
      }
      setPinned(false);
      setOpen(false);
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("touchstart", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("touchstart", handlePointerDown);
    };
  }, [pinned]);

  function show() {
    if (!pinned) setOpen(true);
  }

  function hide() {
    if (!pinned) setOpen(false);
  }

  function togglePin(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault();
    event.stopPropagation();
    setPinned((prev) => {
      const next = !prev;
      setOpen(next);
      return next;
    });
  }

  const panel =
    visible && mounted ? (
      <div
        ref={panelRef}
        id={tooltipId}
        role="tooltip"
        style={{
          top: position?.top ?? -9999,
          left: position?.left ?? -9999,
          width: TOOLTIP_WIDTH,
          maxWidth: TOOLTIP_MAX_WIDTH,
          minWidth: TOOLTIP_MIN_WIDTH,
          maxHeight: TOOLTIP_MAX_HEIGHT,
          visibility: position ? "visible" : "hidden",
        }}
        className="pointer-events-auto fixed z-[9999] overflow-y-auto rounded border border-primary/70 bg-[#060e20] px-3.5 py-3 font-mono shadow-[0_8px_24px_rgba(0,0,0,0.55)] normal-case tracking-normal"
      >
        {position && (
          <span
            aria-hidden
            className="absolute h-0 w-0 border-x-[6px] border-x-transparent"
            style={{
              left: position.arrowOffset,
              ...(position.arrowPlacement === "top"
                ? {
                    top: -6,
                    borderBottom: "6px solid rgb(6 14 32 / 0.95)",
                  }
                : {
                    bottom: -6,
                    borderTop: "6px solid rgb(6 14 32 / 0.95)",
                  }),
            }}
          />
        )}
        <TooltipBody content={content} />
      </div>
    ) : null;

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label="Parameter help"
        aria-describedby={visible ? tooltipId : undefined}
        aria-expanded={visible}
        className="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border border-primary/40 font-mono text-[10px] leading-none text-primary/70 hover:border-primary hover:text-primary"
        onMouseEnter={show}
        onMouseLeave={hide}
        onClick={togglePin}
        onBlur={() => {
          if (!pinned) setOpen(false);
        }}
      >
        ?
      </button>
      {mounted && panel ? createPortal(panel, document.body) : null}
    </>
  );
}

export function ParamLabel({
  children,
  tooltip,
}: {
  children: React.ReactNode;
  tooltip: ParamTooltipContent;
}) {
  return (
    <span className="inline-flex items-center gap-1">
      {children}
      <ParamTooltip content={tooltip} />
    </span>
  );
}
