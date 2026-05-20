import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { BottomNav } from "@/components/BottomNav";
import { Icon } from "@/components/Icon";

export const Route = createFileRoute("/auditoria")({
  head: () => ({
    meta: [
      { title: "Faro UNRaf — Panel de Auditoría" },
      {
        name: "description",
        content:
          "Panel exclusivo para maestros: auditá las interacciones de la IA con los alumnos y dejá feedback.",
      },
      { property: "og:title", content: "Faro UNRaf — Panel de Auditoría" },
      {
        property: "og:description",
        content: "Calificá las respuestas de la IA y aportá feedback pedagógico.",
      },
    ],
  }),
  component: AuditoriaPanel,
});

type LogMaestro = {
  id: string | number;
  pregunta: string;
  respuesta: string;
  alumno_id?: string | number;
  fecha?: string;
  calificacion?: "buena" | "mala" | null;
  comentario?: string | null;
};

type EvalState = {
  calificacion: "buena" | "mala" | null;
  comentario: string;
  estado: "idle" | "enviando" | "ok" | "error";
  mensaje?: string;
};

function AuditoriaPanel() {
  const [logs, setLogs] = useState<LogMaestro[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [evals, setEvals] = useState<Record<string | number, EvalState>>({});

  const API = import.meta.env.VITE_API_URL ?? "";

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/logs-maestros`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const list: LogMaestro[] = Array.isArray(data) ? data : (data.logs ?? data.items ?? []);
      setLogs(list);
      const seed: Record<string | number, EvalState> = {};
      list.forEach((l) => {
        seed[l.id] = {
          calificacion: l.calificacion ?? null,
          comentario: l.comentario ?? "",
          estado: "idle",
        };
      });
      setEvals(seed);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const update = (id: string | number, patch: Partial<EvalState>) =>
    setEvals((prev) => ({
      ...prev,
      [id]: { ...(prev[id] ?? { calificacion: null, comentario: "", estado: "idle" }), ...patch },
    }));

  const enviarEvaluacion = async (log: LogMaestro) => {
    const e = evals[log.id] ?? { calificacion: null, comentario: "", estado: "idle" };
    if (!e.calificacion && !e.comentario.trim()) {
      update(log.id, { estado: "error", mensaje: "Calificá o dejá un comentario." });
      return;
    }
    update(log.id, { estado: "enviando", mensaje: undefined });
    try {
      const res = await fetch(`${API}/api/logs-maestros/evaluar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          log_id: log.id,
          calificacion: e.calificacion,
          comentario: e.comentario.trim(),
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      update(log.id, { estado: "ok", mensaje: "Evaluación enviada" });
    } catch (err) {
      update(log.id, {
        estado: "error",
        mensaje: err instanceof Error ? err.message : "Error",
      });
    }
  };

  return (
    <div className="min-h-screen bg-surface pb-32 md:pb-12">
      <AppHeader anonymousId="MAESTRO" />

      <main className="pt-24 px-4 md:px-12 max-w-6xl mx-auto flex flex-col gap-6">
        <header className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-[12px] font-semibold tracking-[0.25em] text-on-surface-variant uppercase">
              Rol: Maestro
            </p>
            <h1 className="text-3xl md:text-4xl font-extrabold text-primary tracking-tight flex items-center gap-3">
              <Icon name="fact_check" filled className="text-secondary" />
              Panel de Auditoría
            </h1>
            <p className="text-on-surface-variant mt-1 max-w-2xl">
              Revisá las interacciones entre los alumnos y Faro. Calificá la calidad de
              cada respuesta y dejá feedback para mejorar el modelo.
            </p>
          </div>
          <button
            onClick={fetchLogs}
            className="inline-flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-xl font-semibold shadow-md hover:bg-primary-container active:scale-[0.98] transition-all"
          >
            <Icon name="refresh" />
            Actualizar
          </button>
        </header>

        {loading && (
          <div className="rounded-2xl border border-outline-variant/60 bg-white/70 backdrop-blur p-8 text-center text-on-surface-variant flex items-center justify-center gap-2">
            <Icon name="progress_activity" className="animate-spin" />
            Cargando registros…
          </div>
        )}

        {error && !loading && (
          <div className="rounded-2xl border border-red-300 bg-red-50 p-6 text-red-700">
            <p className="font-semibold">No se pudieron cargar los registros.</p>
            <p className="text-sm opacity-80 mt-1">{error}</p>
          </div>
        )}

        {!loading && !error && logs.length === 0 && (
          <div className="rounded-2xl border border-outline-variant/60 bg-white/70 backdrop-blur p-10 text-center text-on-surface-variant">
            Aún no hay interacciones para auditar.
          </div>
        )}

        <section className="flex flex-col gap-4">
          {logs.map((log) => {
            const e = evals[log.id] ?? {
              calificacion: null,
              comentario: "",
              estado: "idle" as const,
            };
            return (
              <article
                key={log.id}
                className="rounded-2xl border border-outline-variant/60 bg-white/80 backdrop-blur card-shadow overflow-hidden"
              >
                <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-outline-variant/40">
                  <div className="p-5 flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-secondary font-semibold text-sm uppercase tracking-wider">
                      <Icon name="help" filled />
                      Pregunta del alumno
                      {log.alumno_id && (
                        <span className="ml-auto text-xs text-on-surface-variant font-normal normal-case tracking-normal">
                          #{log.alumno_id}
                        </span>
                      )}
                    </div>
                    <p className="text-[15px] leading-relaxed text-on-surface whitespace-pre-wrap">
                      {log.pregunta}
                    </p>
                    {log.fecha && (
                      <p className="text-xs text-on-surface-variant mt-auto pt-2">
                        {new Date(log.fecha).toLocaleString()}
                      </p>
                    )}
                  </div>
                  <div className="p-5 flex flex-col gap-2 bg-surface-container-low/40">
                    <div className="flex items-center gap-2 text-primary font-semibold text-sm uppercase tracking-wider">
                      <Icon name="smart_toy" filled />
                      Respuesta de la IA
                    </div>
                    <p className="text-[15px] leading-relaxed text-on-surface whitespace-pre-wrap">
                      {log.respuesta}
                    </p>
                  </div>
                </div>

                <div className="border-t border-outline-variant/40 p-5 bg-surface-container-low/60 flex flex-col gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold text-on-surface-variant mr-1">
                      ¿La IA respondió bien?
                    </span>
                    <button
                      type="button"
                      onClick={() => update(log.id, { calificacion: "buena" })}
                      className={
                        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold border transition-all " +
                        (e.calificacion === "buena"
                          ? "bg-secondary text-on-secondary border-secondary shadow"
                          : "bg-white text-on-surface-variant border-outline-variant hover:border-secondary")
                      }
                    >
                      <Icon name="thumb_up" filled={e.calificacion === "buena"} />
                      Buena
                    </button>
                    <button
                      type="button"
                      onClick={() => update(log.id, { calificacion: "mala" })}
                      className={
                        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold border transition-all " +
                        (e.calificacion === "mala"
                          ? "bg-red-500 text-white border-red-500 shadow"
                          : "bg-white text-on-surface-variant border-outline-variant hover:border-red-400")
                      }
                    >
                      <Icon name="thumb_down" filled={e.calificacion === "mala"} />
                      Mala
                    </button>
                  </div>

                  <textarea
                    value={e.comentario}
                    onChange={(ev) => update(log.id, { comentario: ev.target.value })}
                    placeholder="Comentario de feedback (opcional)…"
                    rows={2}
                    className="w-full rounded-xl border border-outline-variant bg-white px-3 py-2 text-[14px] outline-none focus:ring-2 focus:ring-secondary transition-all resize-y"
                  />

                  <div className="flex items-center gap-3 flex-wrap">
                    <button
                      type="button"
                      onClick={() => enviarEvaluacion(log)}
                      disabled={e.estado === "enviando"}
                      className="inline-flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-xl font-semibold shadow-md hover:bg-primary-container active:scale-[0.98] transition-all disabled:opacity-60"
                    >
                      <Icon
                        name={e.estado === "enviando" ? "progress_activity" : "send"}
                        className={e.estado === "enviando" ? "animate-spin" : ""}
                      />
                      {e.estado === "enviando" ? "Enviando…" : "Enviar evaluación"}
                    </button>
                    {e.estado === "ok" && (
                      <span className="text-sm text-secondary font-semibold inline-flex items-center gap-1">
                        <Icon name="check_circle" filled /> {e.mensaje ?? "Enviada"}
                      </span>
                    )}
                    {e.estado === "error" && (
                      <span className="text-sm text-red-600 font-semibold inline-flex items-center gap-1">
                        <Icon name="error" filled /> {e.mensaje}
                      </span>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </section>
      </main>

      <BottomNav />
    </div>
  );
}
