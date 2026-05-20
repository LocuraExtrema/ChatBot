import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Icon } from "@/components/Icon";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Faro UNRaf — Inicio" },
      {
        name: "description",
        content:
          "Tu guía inteligente para navegar la vida universitaria. Comenzá tu trayectoria con Faro UNRaf.",
      },
      { property: "og:title", content: "Faro UNRaf — Inicio" },
      {
        property: "og:description",
        content: "Recursos, orientación académica y respuestas instantáneas.",
      },
    ],
  }),
  component: Portada,
});

function Portada() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const beamRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!beamRef.current) return;
      const x = (e.clientX / window.innerWidth) * 100;
      const y = (e.clientY / window.innerHeight) * 100;
      beamRef.current.style.background = `radial-gradient(circle at ${x}% ${y}%, rgba(0, 169, 198, 0.10) 0%, transparent 55%)`;
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  const start = () => {
    setLoading(true);
    setTimeout(() => navigate({ to: "/chatbot" }), 700);
  };

  return (
    <main className="relative h-screen w-full overflow-hidden flex flex-col items-center justify-center px-6 bg-surface">
      <div
        ref={beamRef}
        aria-hidden
        className="pointer-events-none absolute inset-0 z-0"
        style={{
          background:
            "radial-gradient(circle at 50% 50%, rgba(0, 169, 198, 0.08) 0%, transparent 60%)",
        }}
      />
      {/* Decorative concentric rings = lighthouse beam */}
      <div
        aria-hidden
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[120vmin] h-[120vmin] rounded-full opacity-40 z-0"
        style={{
          background:
            "radial-gradient(circle, transparent 35%, rgba(120,143,222,0.10) 36%, transparent 38%, transparent 55%, rgba(0,104,122,0.06) 56%, transparent 58%)",
        }}
      />

      <div className="relative z-10 flex flex-col items-center max-w-3xl text-center animate-in fade-in zoom-in-95 duration-1000">
        {/* Logo / Lighthouse mark */}
        <div className="mb-10 flex flex-col items-center">
          <div className="relative w-28 h-28 mb-6 grid place-items-center">
            <div className="absolute inset-0 rounded-full bg-secondary/15 blur-2xl" />
            <div className="relative w-24 h-24 rounded-full bg-primary text-on-primary grid place-items-center floating-shadow">
              <Icon
                name="light_mode"
                filled
                className="text-[44px] text-tertiary-fixed-dim"
              />
            </div>
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold text-primary tracking-tight leading-[1.05]">
            Faro <span className="text-secondary">UNRaf</span>
          </h1>
          <p className="mt-3 text-[13px] font-semibold tracking-[0.3em] text-on-surface-variant uppercase">
            Guidance through Clarity
          </p>
        </div>

        <p className="max-w-xl text-on-surface-variant text-lg leading-relaxed mb-12">
          Tu guía inteligente para navegar la vida universitaria. Encontrá recursos,
          orientación académica y respuestas instantáneas en un solo lugar.
        </p>

        <button
          onClick={start}
          disabled={loading}
          className="group inline-flex items-center gap-3 bg-primary text-on-primary font-bold text-xl md:text-2xl px-10 py-5 rounded-2xl floating-shadow transition-all duration-300 hover:-translate-y-1 hover:scale-[1.03] active:scale-[0.98] disabled:opacity-80"
        >
          {loading ? (
            <>
              <Icon name="progress_activity" className="animate-spin" />
              Cargando...
            </>
          ) : (
            <>
              COMENZAR
              <Icon
                name="arrow_forward"
                className="transition-transform group-hover:translate-x-1"
              />
            </>
          )}
        </button>
      </div>

      <footer className="absolute bottom-6 left-0 right-0 z-10 flex justify-center items-center gap-2 text-on-surface-variant/70">
        <Icon name="school" className="text-[18px]" />
        <span className="text-[12px] font-semibold tracking-[0.25em]">
          UNIVERSIDAD NACIONAL DE RAFAELA
        </span>
      </footer>

      {/* Transition overlay */}
      <div
        className={
          "fixed inset-0 z-[100] bg-primary transition-transform duration-700 ease-in-out " +
          (loading ? "translate-y-0" : "translate-y-full")
        }
      />
    </main>
  );
}
