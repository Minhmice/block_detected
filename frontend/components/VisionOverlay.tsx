"use client";

import { useEffect, useRef } from "react";
import type { RefObject } from "react";

import { useVisionStore } from "@/stores/useVisionStore";

const NATIVE_W = 640;
const NATIVE_H = 480;

export function VisionOverlay({
  imgRef,
}: {
  imgRef: RefObject<HTMLImageElement | null>;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const latestResult = useVisionStore((s) => s.latestResult);
  const latestValid = useVisionStore((s) => s.latestValid);
  const overlayFlags = useVisionStore((s) => s.overlayFlags);

  useEffect(() => {
    let raf = 0;
    const draw = () => {
      const img = imgRef.current;
      const canvas = canvasRef.current;
      if (!img || !canvas) {
        raf = requestAnimationFrame(draw);
        return;
      }
      const rect = img.getBoundingClientRect();
      canvas.style.left = `${img.offsetLeft}px`;
      canvas.style.top = `${img.offsetTop}px`;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      canvas.width = Math.round(rect.width);
      canvas.height = Math.round(rect.height);

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const scaleX = rect.width / NATIVE_W;
      const scaleY = rect.height / NATIVE_H;

      const sx = (x: number) => x * scaleX;
      const sy = (y: number) => y * scaleY;

      if (overlayFlags.grid) {
        ctx.strokeStyle = "rgba(76, 215, 246, 0.25)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(canvas.width / 2, 0);
        ctx.lineTo(canvas.width / 2, canvas.height);
        ctx.moveTo(0, canvas.height / 2);
        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
      }

      if (!latestValid || !latestResult?.cornersPx) {
        raf = requestAnimationFrame(draw);
        return;
      }

      const { tl, tr, br, bl } = latestResult.cornersPx;

      if (overlayFlags.bbox) {
        const xs = [tl.x, tr.x, br.x, bl.x].map(sx);
        const ys = [tl.y, tr.y, br.y, bl.y].map(sy);
        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);
        ctx.strokeStyle = "#4edea3";
        ctx.lineWidth = 2;
        ctx.strokeRect(minX, minY, maxX - minX, maxY - minY);
      }

      if (overlayFlags.squareCorners) {
        ctx.strokeStyle = "#4cd7f6";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(sx(tl.x), sy(tl.y));
        ctx.lineTo(sx(tr.x), sy(tr.y));
        ctx.lineTo(sx(br.x), sy(br.y));
        ctx.lineTo(sx(bl.x), sy(bl.y));
        ctx.closePath();
        ctx.stroke();
        for (const p of [tl, tr, br, bl]) {
          ctx.fillStyle = "#4cd7f6";
          ctx.fillRect(sx(p.x) - 3, sy(p.y) - 3, 6, 6);
        }
      }

      if (overlayFlags.center && latestResult.centerPx) {
        const cx = sx(latestResult.centerPx.x);
        const cy = sy(latestResult.centerPx.y);
        ctx.fillStyle = "#ffb4ab";
        ctx.beginPath();
        ctx.arc(cx, cy, 4, 0, Math.PI * 2);
        ctx.fill();
      }

      if (overlayFlags.angle && latestResult.angleDeg != null) {
        const cx = latestResult.centerPx
          ? sx(latestResult.centerPx.x)
          : canvas.width / 2;
        const cy = latestResult.centerPx
          ? sy(latestResult.centerPx.y)
          : canvas.height / 2;
        const rad = (latestResult.angleDeg * Math.PI) / 180;
        ctx.strokeStyle = "#4cd7f6";
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(rad) * 40, cy + Math.sin(rad) * 40);
        ctx.stroke();
      }

      if (overlayFlags.pickup && latestResult.pickupPoseMm) {
        const p = latestResult.pickupPoseMm;
        ctx.fillStyle = "#dae2fd";
        ctx.font = "12px JetBrains Mono, monospace";
        ctx.fillText(
          `PICK ${p.xMm.toFixed(1)}mm ${p.yMm.toFixed(1)}mm θ${p.thetaDeg.toFixed(1)}°`,
          8,
          canvas.height - 8,
        );
      }

      raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [imgRef, latestResult, latestValid, overlayFlags]);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute left-0 top-0"
      aria-hidden
    />
  );
}
