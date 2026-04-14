import React, { useEffect, useRef, memo } from 'react';

/* ─── Seeded PRNG (mulberry32) ─────────────────────────────────────── */
function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ─── Path builder ─────────────────────────────────────────────────── */
interface PathConfig {
  seed: number;
  width: number;
  height: number;
  yBand: [number, number]; // fraction of height [min, max]
  cpRange: number;          // max control-point y-deviation in px
}

function buildPath({ seed, width, height, yBand, cpRange }: PathConfig): string {
  const rng = mulberry32(seed);
  const yMin = height * yBand[0];
  const yMax = height * yBand[1];
  const startY = yMin + rng() * (yMax - yMin);

  // ~5-7 cubic bezier segments across width
  const segments = 5 + Math.floor(rng() * 3);
  const segW = width / segments;

  let d = `M 0 ${startY.toFixed(1)}`;
  let curX = 0;
  let curY = startY;

  for (let i = 0; i < segments; i++) {
    const nextX = curX + segW;
    const nextY = yMin + rng() * (yMax - yMin);
    const cp1x = curX + segW * (0.25 + rng() * 0.2);
    const cp1y = curY + (rng() - 0.5) * 2 * cpRange;
    const cp2x = curX + segW * (0.55 + rng() * 0.2);
    const cp2y = nextY + (rng() - 0.5) * 2 * cpRange;
    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${nextX.toFixed(1)} ${nextY.toFixed(1)}`;
    curX = nextX;
    curY = nextY;
  }
  return d;
}

/* ─── Layer definitions ─────────────────────────────────────────────── */
interface LayerDef {
  id: string;
  count: number;
  strokeWidth: [number, number];
  opacity: [number, number];
  duration: [number, number];
  color: string;
  glow: boolean;
  yBand: [number, number];
  cpRange: number;
  dashArray: string;
  swayAmp: number;
  swayDuration: number;
  parallaxFactor: number; // mouse parallax multiplier
}

const LAYERS: LayerDef[] = [
  {
    id: 'bg',
    count: 8,
    strokeWidth: [0.8, 1.5],
    opacity: [0.18, 0.35],
    duration: [26, 38],
    color: '#7a5c0a',
    glow: false,
    yBand: [0.1, 0.9],
    cpRange: 90,
    dashArray: '2000 600',
    swayAmp: 18,
    swayDuration: 30,
    parallaxFactor: 0.008,
  },
  {
    id: 'mid',
    count: 12,
    strokeWidth: [1.5, 2.5],
    opacity: [0.35, 0.58],
    duration: [16, 24],
    color: '#c8960c',
    glow: false,
    yBand: [0.15, 0.85],
    cpRange: 70,
    dashArray: '2000 600',
    swayAmp: 30,
    swayDuration: 22,
    parallaxFactor: 0.018,
  },
  {
    id: 'fg',
    count: 10,
    strokeWidth: [2.5, 5.0],
    opacity: [0.58, 0.85],
    duration: [8, 15],
    color: '#f5a623',
    glow: true,
    yBand: [0.2, 0.8],
    cpRange: 50,
    dashArray: '2000 600',
    swayAmp: 48,
    swayDuration: 16,
    parallaxFactor: 0.032,
  },
];

/* ─── CSS ───────────────────────────────────────────────────────────── */
function buildCSS(W: number, H: number): string {
  return `
    @keyframes sandFlow {
      0%   { stroke-dashoffset: 2600; }
      100% { stroke-dashoffset: 0; }
    }
    @keyframes sbSway0 {
      0%, 100% { transform: translateX(0px); }
      50%       { transform: translateX(18px); }
    }
    @keyframes sbSway1 {
      0%, 100% { transform: translateX(0px); }
      50%       { transform: translateX(-30px); }
    }
    @keyframes sbSway2 {
      0%, 100% { transform: translateX(0px); }
      50%       { transform: translateX(48px); }
    }
    @media (prefers-reduced-motion: reduce) {
      .sb-path { animation: none !important; }
      .sb-layer { animation: none !important; }
    }
  `;
}

/* ─── Component ─────────────────────────────────────────────────────── */
const SandBackground = memo(function SandBackground() {
  const W = 1440;
  const H = 900;

  const layerRefs = useRef<(SVGSVGElement | null)[]>([null, null, null]);
  const rafRef = useRef<number | null>(null);
  const mouseRef = useRef({ x: 0, y: 0 });
  const targetRef = useRef({ x: 0, y: 0 });

  /* Mouse tracking */
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      // Normalise to [-1, 1]
      targetRef.current.x = (e.clientX / window.innerWidth - 0.5) * 2;
      targetRef.current.y = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener('mousemove', onMove, { passive: true });

    const animate = () => {
      // Ease toward target
      mouseRef.current.x += (targetRef.current.x - mouseRef.current.x) * 0.05;
      mouseRef.current.y += (targetRef.current.y - mouseRef.current.y) * 0.05;

      layerRefs.current.forEach((svg, i) => {
        if (!svg) return;
        const factor = LAYERS[i].parallaxFactor;
        const tx = mouseRef.current.x * factor * W;
        const ty = mouseRef.current.y * factor * H;
        svg.style.transform = `translate(${tx.toFixed(2)}px, ${ty.toFixed(2)}px)`;
      });

      rafRef.current = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener('mousemove', onMove);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  /* Build path data per layer */
  const layerPaths = LAYERS.map((layer, li) => {
    const rng = mulberry32(li * 1000 + 42);
    return Array.from({ length: layer.count }, (_, pi) => {
      const seed = li * 100 + pi * 7 + 1;
      const rw = mulberry32(seed + 9999);
      const strokeWidth = layer.strokeWidth[0] + rw() * (layer.strokeWidth[1] - layer.strokeWidth[0]);
      const opacity = layer.opacity[0] + rw() * (layer.opacity[1] - layer.opacity[0]);
      const duration = layer.duration[0] + rw() * (layer.duration[1] - layer.duration[0]);
      const delay = rw() * -duration; // random start phase

      const d = buildPath({
        seed,
        width: W,
        height: H,
        yBand: layer.yBand,
        cpRange: layer.cpRange,
      });

      // Gradient id unique per path
      const gradId = `sg-${layer.id}-${pi}`;
      const filterId = `glow-${layer.id}`;

      return { d, strokeWidth, opacity, duration, delay, gradId, filterId };
    });
  });

  const noiseDataUri = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.08'/%3E%3C/svg%3E")`;

  return (
    <div
      aria-hidden="true"
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        background: 'linear-gradient(160deg, #0a0805 0%, #110e06 40%, #0d0c08 70%, #0a0905 100%)',
        zIndex: 0,
      }}
    >
      {/* Injected CSS animations */}
      <style dangerouslySetInnerHTML={{ __html: buildCSS(W, H) }} />

      {/* Noise texture overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: noiseDataUri,
          backgroundRepeat: 'repeat',
          opacity: 0.35,
          pointerEvents: 'none',
          zIndex: 1,
        }}
      />

      {/* SVG Layers */}
      {LAYERS.map((layer, li) => (
        <svg
          key={layer.id}
          ref={(el) => { layerRefs.current[li] = el; }}
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="xMidYMid slice"
          className={`sb-layer`}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            zIndex: 2 + li,
            willChange: 'transform',
            animation: `sbSway${li} ${layer.swayDuration}s ease-in-out infinite`,
            overflow: 'visible',
          }}
        >
          <defs>
            {/* Glow filter for foreground layer */}
            {layer.glow && (
              <filter id={`glow-${layer.id}`} x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2.5" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            )}

            {/* Linear gradients: transparent → color → transparent along path width */}
            {layerPaths[li].map(({ gradId }) => (
              <linearGradient key={gradId} id={gradId} x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%"   stopColor={layer.color} stopOpacity="0.15" />
                <stop offset="8%"   stopColor={layer.color} stopOpacity="1" />
                <stop offset="92%"  stopColor={layer.color} stopOpacity="1" />
                <stop offset="100%" stopColor={layer.color} stopOpacity="0.15" />
              </linearGradient>
            ))}
          </defs>

          {layerPaths[li].map(({ d, strokeWidth, opacity, duration, delay, gradId, filterId }, pi) => (
            <path
              key={pi}
              d={d}
              fill="none"
              stroke={`url(#${gradId})`}
              strokeWidth={strokeWidth}
              opacity={opacity}
              strokeLinecap="round"
              filter={layer.glow ? `url(#${filterId})` : undefined}
              className="sb-path"
              style={{
                strokeDasharray: layer.dashArray,
                strokeDashoffset: 2600,
                animation: `sandFlow ${duration.toFixed(1)}s linear ${delay.toFixed(1)}s infinite`,
              }}
            />
          ))}
        </svg>
      ))}

      {/* Dune silhouette at bottom */}
      <svg
        viewBox="0 0 1440 200"
        preserveAspectRatio="none"
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          width: '100%',
          height: '160px',
          zIndex: 6,
          pointerEvents: 'none',
        }}
      >
        <path
          d="M0 200 L0 130 Q 120 60, 280 110 Q 440 160, 580 80 Q 720 0, 860 70 Q 1000 140, 1140 90 Q 1280 40, 1440 100 L1440 200 Z"
          fill="#0a0805"
          opacity="0.85"
        />
        <path
          d="M0 200 L0 155 Q 180 120, 360 150 Q 540 180, 720 140 Q 900 100, 1080 148 Q 1260 185, 1440 155 L1440 200 Z"
          fill="#0d0c08"
          opacity="0.9"
        />
      </svg>

      {/* Radial vignette + dark overlay for text readability */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse 80% 60% at 50% 50%, transparent 30%, rgba(0,0,0,0.55) 100%)',
          zIndex: 7,
          pointerEvents: 'none',
        }}
      />
      {/* Bottom fade to match site bg */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '160px',
          background: 'linear-gradient(to bottom, transparent, #0D0D0D)',
          zIndex: 8,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
});

export default SandBackground;
