'use client';

import React, { useEffect, useRef } from 'react';

export function AstraPlanetaryBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    // Particle nodes for 3D neural network effect
    const particleCount = width < 768 ? 35 : 65;
    const particles: Array<{
      x: number;
      y: number;
      vx: number;
      vy: number;
      radius: number;
      color: string;
      alpha: number;
    }> = [];

    const colors = ['#38bdf8', '#818cf8', '#06b6d4', '#c084fc', '#60a5fa'];

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * (height * 0.75), // Concentrate in upper and mid horizon
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: Math.random() * 2 + 1,
        color: colors[Math.floor(Math.random() * colors.length)],
        alpha: Math.random() * 0.6 + 0.2,
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw subtle connecting neural lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          const maxDist = width < 768 ? 75 : 110;
          if (dist < maxDist) {
            const lineAlpha = (1 - dist / maxDist) * 0.18;
            ctx.beginPath();
            ctx.strokeStyle = `rgba(56, 189, 248, ${lineAlpha})`;
            ctx.lineWidth = 0.75;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw glowing particle nodes
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        // Bounce off bounds
        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height * 0.8) p.vy *= -1;

        ctx.save();
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = 8;
        ctx.globalAlpha = p.alpha;
        ctx.fill();
        ctx.restore();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none z-0 bg-[#06080e]">
      {/* 1. Deep Space Cosmic Nebula Base */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse 80% 60% at 50% 20%, rgba(15, 23, 42, 0.7) 0%, #05070c 100%)'
        }}
      />

      {/* 2. Interactive 3D Neural Particle Canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
      />

      {/* 3. Deep Atmospheric Diffuse Glow */}
      <div 
        className="absolute -bottom-40 left-1/2 -translate-x-1/2 w-[160vw] max-w-[2000px] h-[550px] rounded-[100%] pointer-events-none animate-planet-glow"
        style={{
          background: 'radial-gradient(ellipse at 50% 30%, rgba(30, 64, 175, 0.32) 0%, rgba(6, 182, 212, 0.22) 35%, rgba(59, 130, 246, 0.08) 65%, transparent 80%)',
          filter: 'blur(50px)',
        }}
      />

      {/* 4. Realistic Curved Planet Horizon Sphere */}
      <div 
        className="absolute -bottom-[540px] sm:-bottom-[640px] left-1/2 -translate-x-1/2 w-[180vw] max-w-[2400px] h-[950px] rounded-[100%] overflow-hidden"
        style={{
          boxShadow: '0 -15px 50px -10px rgba(56, 189, 248, 0.45), 0 -4px 30px 0px rgba(96, 165, 250, 0.75), 0 -80px 140px -20px rgba(37, 99, 235, 0.35)',
          background: 'radial-gradient(ellipse at 50% 0%, #0d234a 0%, #07152e 25%, #050c1b 50%, #03060d 85%)',
          borderTop: '1.5px solid rgba(186, 230, 253, 0.9)',
        }}
      >
        {/* Subtle Atmospheric Haze on Horizon Rim */}
        <div 
          className="absolute inset-x-0 top-0 h-40 pointer-events-none"
          style={{
            background: 'linear-gradient(180deg, rgba(56, 189, 248, 0.28) 0%, rgba(37, 99, 235, 0.15) 30%, rgba(15, 23, 42, 0.02) 80%, transparent 100%)',
          }}
        />

        {/* Planet Surface Continents / Ocean Glow Details */}
        <div 
          className="absolute inset-0 opacity-45 mix-blend-screen"
          style={{
            backgroundImage: `
              radial-gradient(ellipse 40% 25% at 35% 20%, rgba(34, 211, 238, 0.28) 0%, transparent 70%),
              radial-gradient(ellipse 50% 30% at 65% 25%, rgba(59, 130, 246, 0.32) 0%, transparent 75%),
              radial-gradient(ellipse 30% 20% at 50% 15%, rgba(147, 197, 253, 0.22) 0%, transparent 60%)
            `,
          }}
        />
      </div>

      {/* 5. Delicate Lens Flare Glow in Center */}
      <div 
        className="absolute bottom-16 left-1/2 -translate-x-1/2 w-80 h-28 rounded-full opacity-45 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at 50% 50%, rgba(125, 211, 252, 0.4) 0%, rgba(59, 130, 246, 0.12) 50%, transparent 80%)',
          filter: 'blur(25px)',
        }}
      />
    </div>
  );
}
