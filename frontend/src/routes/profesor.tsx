import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { BottomNav } from "@/components/BottomNav";
import { Icon } from "@/components/Icon";
import { useLti, type ChatMessage } from "@/lib/lti-context";

export const Route = createFileRoute("/profesor")({
  head: () => ({
    meta: [
      { title: "Faro UNRaf — Vista del Profesor" },
      {
        name: "description",
        content:
          "Auditá el historial del chat actual y calificá las respuestas de la IA con feedback.",
      },
      { property: "og:title", content: "Faro UNRaf — Vista del Profesor" },
      {
        property: "og:description",
        content: "Calificación rápida y corrección sugerida para cada respuesta de la IA.",
      },
    ],
  }),
  component: ProfesorView,
});

type Pair = {
  pregunta: ChatMessage;
  respuesta: ChatMessage;
};

type Calificacion = "positivo" | "negativo";

type FeedbackState = {
  calificacion: Calificacion | null;
  correccion: string;
  estado: "idle" | "enviando" | "ok" | "error";
  mensaje?: string;
};

function buildPairs(messages: ChatMessage[]): Pair[] {
  const pairs: Pair[] = [];
  for (let i = 0; i < messages.length; i++) {
    const m = messages[i];
    if (m.role !== "user") continue;
    const reply = messages
      .slice(i + 1)
      .find((n) => n.role === "ai" && (n.inReplyTo === m.id || true));
    if (reply) pairs.push({ pregunta: m, respuesta: reply });
  }
  return pairs;
}

function ProfesorView() {
  const { user, messages, setUser } = useLti();

  // Si el rol global no es Instructor, ofrecemos cambiarlo para esta sesión.
  const [feedback, setFeedback] = useState<Record<string, FeedbackState>>({});
  const pairs = useMemo(() => buildPairs(messages), [messages]);

  const update = (id: string, patch: Partial<FeedbackState>) =>
    setFeedback((prev) => ({
      ...prev,
      [id]: {
        ...(prev[id] ?? { calificacion: null, correccion: "", estado: "idle" as const }),
        ...patch,
      },
    }));

  const enviar = async (p: Pair) => {
    const f = feedback[p.respuesta.id] ?? {
      calificacion: null,
      correccion: "",
      estado: "idle" as const,
    };
    if (!f.calificacion) {
      update(p.respuesta.id, { estado: "error", mensaje: "Elegí una calificación." });
      return;
    }
    update(p.respuesta.id, { estado: "enviando", mensaje: undefined });
    try {
      const base = import.meta.env.VITE_API_URL ?? "";
      const res = await fetch(`${base}/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: user.email,
          pregunta_original: p.pregunta.text,
          respuesta_bot: p.respuesta.text,
          calificacion: f.calificacion,
          correccion_sugerida: f.calificacion === "negativo" ? f.correccion.trim() : "",
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      update(p.respuesta.id, { estado: "ok", mensaje: "Feedback enviado" });
    } catch (err) {
      update(p.respuesta.id, {
        estado: "error",
        mensaje: err instanceof Error ? err.message : "Error",
      });
    }
  };

  return (
    <div className="min-h-screen bg-surface pb-32 md:pb-12">
      <AppHeader anonymousId="PROF" />

      <main className="pt-24 px-4 md:px-12 max-w-5xl mx-auto flex flex-col gap-6">
        <header className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-[12px] font-semibold tracking-[0.25em] text-on-surface-variant uppercase">
              Rol: {user.role}
            </p>
            <h1 className="text-3xl md:text-4xl font-extrabold text-primary tracking-tight flex items-center gap-3">
              <Icon name="reviews" filled className="text-secondary" />
              Vista del Profesor
            </h1>
            <p className="text-on-surface-variant mt-1 max-w-2xl">
              Auditá el historial del chat actual y calificá cada respuesta de la IA.
              Si marcás <span className="font-semibold text-red-600">Mal resultado</span>{" "}
              podés sugerir una corrección.
            </p>
            <p className="text-xs text-on-surface-variant mt-2">
              Profesor: <span className="font-semibold">{user.email}</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            {user.role !== "Instructor" && (
              <button
                onClick={() =>
                  setUser({
                    ...user,
                    role: "Instructor",
                    email: "profesor@unraf.edu.ar",
                  })
                }
                className="inline-flex items-center gap-2 bg-secondary text-on-secondary px-3 py-2 rounded-xl font-semibold text-sm shadow-md hover:opacity-90 active:scale-[0.98] transition-all"
              >
                <Icon name="switch_account" />
                Entrar como Instructor
              </button>
            )}
            <Link
              to="/chatbot"
              className="inline-flex items-center gap-2 bg-primary text-on-primary px-3 py-2 rounded-xl font-semibold text-sm shadow-md hover:bg-primary-container active:scale-[0.98] transition-all"
            >
              <Icon name="chat" />
              Ir al chat
            </Link>
          </div>
        </header>

        {pairs.length === 0 && (
          <div className="rounded-2xl border border-outline-variant/60 bg-white/70 backdrop-blur p-10 text-center text-on-surface-variant">
            Todavía no hay interacciones en este chat. Pedile al alumno que envíe una
            pregunta desde la vista del Chatbot.
          </div>
        )}

        <section className="flex flex-col gap-4">
          {pairs.map((p, i) => {
            const f = feedback[p.respuesta.id] ?? {
              calificacion: null,
              correccion: "",
              estado: "idle" as const,
            };
            return (
              <article
                key={p.respuesta.id}
                className="rounded-2xl border border-outline-variant/60 bg-white/80 backdrop-blur card-shadow overflow-hidden"
              >
                <div className="px-5 py-2.5 bg-surface-container-low/60 text-xs font-semibold uppercase tracking-wider text-on-surface-variant border-b border-outline-variant/40">
                  Intercambio #{i + 1}
                </div>

                <div className="p-5 flex flex-col gap-2 border-b border-outline-variant/40">
                  <div className="flex items-center gap-2 text-secondary font-semibold text-sm uppercase tracking-wider">
                    <Icon name="help" filled />
                    Pregunta del alumno
                  </div>
                  <p className="text-[15px] leading-relaxed text-on-surface whitespace-pre-wrap">
                    {p.pregunta.text}
                  </p>
                </div>

                <div className="grid md:grid-cols-[1fr_auto] gap-5 p-5 items-start">
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2 text-primary font-semibold text-sm uppercase tracking-wider">
                      <Icon name="smart_toy" filled />
                      Respuesta de la IA
                    </div>
                    <p className="text-[15px] leading-relaxed text-on-surface whitespace-pre-wrap">
                      {p.respuesta.text}
                    </p>
                  </div>

                  <div className="flex md:flex-col gap-2 md:min-w-[180px]">
                    <button
                      type="button"
                      onClick={() => update(p.respuesta.id, { calificacion: "positivo" })}
                      className={
                        "inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-sm font-semibold border transition-all flex-1 " +
                        (f.calificacion === "positivo"
                          ? "bg-secondary text-on-secondary border-secondary shadow"
                          : "bg-white text-on-surface-variant border-outline-variant hover:border-secondary")
                      }
                    >
                      <Icon name="thumb_up" filled={f.calificacion === "positivo"} />
                      Buen resultado
                    </button>
                    <button
                      type="button"
                      onClick={() => update(p.respuesta.id, { calificacion: "negativo" })}
                      className={
                        "inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-sm font-semibold border transition-all flex-1 " +
                        (f.calificacion === "negativo"
                          ? "bg-red-500 text-white border-red-500 shadow"
                          : "bg-white text-on-surface-variant border-outline-variant hover:border-red-400")
                      }
                    >
                      <Icon name="thumb_down" filled={f.calificacion === "negativo"} />
                      Mal resultado
                    </button>
                  </div>
                </div>

                {f.calificacion === "negativo" && (
                  <div className="px-5 pb-3 -mt-2 animate-in fade-in slide-in-from-top-1 duration-200">
                    <label className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                      Corrección sugerida (opcional)
                    </label>
                    <textarea
                      value={f.correccion}
                      onChange={(ev) =>
                        update(p.respuesta.id, { correccion: ev.target.value })
                      }
                      placeholder="¿Qué debería haber respondido la IA?"
                      rows={3}
                      className="mt-1 w-full rounded-xl border border-outline-variant bg-white px-3 py-2 text-[14px] outline-none focus:ring-2 focus:ring-secondary transition-all resize-y"
                    />
                  </div>
                )}

                <div className="px-5 pb-5 pt-2 flex items-center gap-3 flex-wrap">
                  <button
                    type="button"
                    onClick={() => enviar(p)}
                    disabled={f.estado === "enviando" || !f.calificacion}
                    className="inline-flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-xl font-semibold shadow-md hover:bg-primary-container active:scale-[0.98] transition-all disabled:opacity-60"
                  >
                    <Icon
                      name={f.estado === "enviando" ? "progress_activity" : "send"}
                      className={f.estado === "enviando" ? "animate-spin" : ""}
                    />
                    {f.estado === "enviando" ? "Enviando…" : "Confirmar feedback"}
                  </button>
                  {f.estado === "ok" && (
                    <span className="text-sm text-secondary font-semibold inline-flex items-center gap-1">
                      <Icon name="check_circle" filled /> {f.mensaje ?? "Enviado"}
                    </span>
                  )}
                  {f.estado === "error" && (
                    <span className="text-sm text-red-600 font-semibold inline-flex items-center gap-1">
                      <Icon name="error" filled /> {f.mensaje}
                    </span>
                  )}
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
