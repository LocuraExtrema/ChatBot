import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { BottomNav } from "@/components/BottomNav";
import { Icon } from "@/components/Icon";
import { useLti } from "@/lib/lti-context";

// Librerías para renderizar Markdown y Ecuaciones Matemáticas (LaTeX)
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css"; // Estilos de KaTeX para los símbolos matemáticos

export const Route = createFileRoute("/chatbot")({
  head: () => ({
    meta: [
      { title: "Faro UNRaf — Chatbot del estudiante" },
      {
        name: "description",
        content:
          "Chateá con Faro y registrá tu nivel de confianza académica de forma anónima.",
      },
      { property: "og:title", content: "Faro UNRaf — Chatbot" },
      {
        property: "og:description",
        content: "Orientación académica anónima en tiempo real.",
      },
    ],
  }),
  component: StudentChat,
});

function StudentChat() {
  const { user, messages, addMessage } = useLti();
  const [input, setInput] = useState("");
  
  // Nivel pedagógico estricto para conectar con main.py (1: Principiante, 2: Intermedio, 3: Avanzado)
  const [confidence, setConfidence] = useState<number>(1);
  const [saved, setSaved] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const [sending, setSending] = useState(false);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    const userMsg = addMessage({ role: "user", text });
    setInput("");
    setSending(true);
    try {
      const base = import.meta.env.VITE_API_URL ?? "";
      const res = await fetch(`${base}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.user_id,
          course_id: user.course_id,
          role: user.role,
          pregunta: text,
          confidence: confidence, // Viaja el nivel estricto al backend
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const reply =
        data.respuesta ?? data.response ?? data.text ?? data.message ?? JSON.stringify(data);
      addMessage({ role: "ai", text: String(reply), inReplyTo: userMsg.id });
    } catch (err) {
      addMessage({
        role: "ai",
        text: `No pude conectarme con el servidor. ${err instanceof Error ? err.message : ""}`,
        inReplyTo: userMsg.id,
      });
    } finally {
      setSending(false);
    }
  };

  const save = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const obtenerNombreNivel = (nivel: number) => {
    if (nivel === 1) return "Principiante";
    if (nivel === 2) return "Intermedio";
    return "Avanzado";
  };

  return (
    <div className="min-h-screen bg-surface pb-32 md:pb-12">
      <AppHeader anonymousId="225" />

      <main className="pt-24 px-4 md:px-20 max-w-2xl mx-auto flex flex-col gap-6">
        <section>
          <p className="text-on-surface-variant">
            Tu identificador anónimo:{" "}
            <span className="font-bold text-primary">#225</span>
          </p>
        </section>

        {/* Chat */}
        <section className="flex flex-col h-[460px] rounded-2xl overflow-hidden border border-outline-variant/60 card-shadow bg-white/70 backdrop-blur">
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-white/40"
            style={{ scrollbarWidth: "thin" }}
          >
            {messages.map((m, i) => {
              // Función interna clave para normalizar los delimitadores matemáticos de Phi-3 a formato $ y $$ válidos
              const formatearTextoMatematico = (texto: string) => {
                if (m.role !== "ai") return texto;
                return texto
                  // Convierte bloques de ecuaciones escapados \[ ... \] o crudos [ ... ] a $$ ... $$
                  .replace(/\\\[/g, "$$").replace(/\\\]/g, "$$")
                  // Convierte fórmulas en línea escapadas \( ... \) o crudas ( ... ) a $ ... $
                  .replace(/\\Ref/g, "$").replace(/\\\)/g, "$")
                  .replace(/\\\(/g, "$");
              };

              return (
                <div
                  key={i}
                  className={
                    "max-w-[85%] px-4 py-3 text-[15px] leading-relaxed animate-in fade-in slide-in-from-bottom-1 duration-300 " +
                    (m.role === "ai"
                      ? "self-start bg-surface-container-highest text-on-surface-variant rounded-2xl rounded-tl-sm"
                      : "self-end bg-primary text-on-primary rounded-2xl rounded-tr-sm shadow-sm")
                  }
                >
                  {/* Si el mensaje viene de la IA, lo procesamos con el formateador antes del renderizado */}
                  {m.role === "ai" ? (
                    <div className="prose prose-sm max-w-none text-on-surface-variant custom-markdown">
                      <ReactMarkdown
                        remarkPlugins={[remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {formatearTextoMatematico(m.text)}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    m.text
                  )}
                </div>
              );
            })}
            {sending && (
              <div className="self-start bg-surface-container-highest text-on-surface-variant rounded-2xl rounded-tl-sm px-4 py-3 text-[15px] italic opacity-80">
                Escribiendo…
              </div>
            )}
          </div>
          <div className="p-3 border-t border-outline-variant/60 bg-white flex items-center gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Escribe un mensaje..."
              disabled={sending}
              className="flex-1 bg-surface-container-low rounded-full px-4 py-2.5 outline-none focus:ring-2 focus:ring-secondary text-[15px] transition-all disabled:opacity-60"
            />
            <button
              onClick={send}
              disabled={sending}
              aria-label="Enviar"
              className="w-11 h-11 grid place-items-center bg-primary text-on-primary rounded-full active:scale-90 transition-transform shadow-md hover:bg-primary-container disabled:opacity-60"
            >
              <Icon name="send" />
            </button>
          </div>
        </section>

        {/* Selector de Nivel Pedagógico Estricto (1 al 3) */}
        <section className="rounded-2xl border border-outline-variant/60 card-shadow bg-white/70 backdrop-blur p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-[20px] font-bold text-primary">
              <Icon name="monitoring" filled className="text-secondary" />
              Nivel Pedagógico
            </h2>
            <div className="bg-secondary-container text-on-secondary-container px-3 py-1 rounded-full text-sm font-bold">
              {obtenerNombreNivel(confidence)}
            </div>
          </div>
          <p className="text-on-surface-variant">
            ¿Con qué nivel de profundidad te gustaría que te responda el docente virtual?
          </p>

          <div className="grid grid-cols-3 gap-2 py-2">
            <button
              onClick={() => setConfidence(1)}
              className={`py-3 px-2 rounded-xl text-xs sm:text-sm font-bold transition-all border ${
                confidence === 1
                  ? "bg-secondary text-white border-secondary shadow-md"
                  : "bg-surface-container-low text-on-surface-variant border-outline-variant hover:bg-surface-container-high"
              }`}
            >
              1. Principiante
            </button>
            <button
              onClick={() => setConfidence(2)}
              className={`py-3 px-2 rounded-xl text-xs sm:text-sm font-bold transition-all border ${
                confidence === 2
                  ? "bg-secondary text-white border-secondary shadow-md"
                  : "bg-surface-container-low text-on-surface-variant border-outline-variant hover:bg-surface-container-high"
              }`}
            >
              2. Intermedio
            </button>
            <button
              onClick={() => setConfidence(3)}
              className={`py-3 px-2 rounded-xl text-xs sm:text-sm font-bold transition-all border ${
                confidence === 3
                  ? "bg-secondary text-white border-secondary shadow-md"
                  : "bg-surface-container-low text-on-surface-variant border-outline-variant hover:bg-surface-container-high"
              }`}
            >
              3. Avanzado
            </button>
          </div>

          <button
            onClick={save}
            className="w-full py-4 bg-primary text-on-primary rounded-xl font-bold flex items-center justify-center gap-2 shadow-md hover:bg-primary-container active:scale-[0.98] transition-all"
          >
            <Icon name={saved ? "check_circle" : "save"} filled={saved} />
            {saved ? "CONFIGURACIÓN GUARDADA" : "GUARDAR CONFIGURACIÓN"}
          </button>
        </section>

        <section className="text-center py-6">
          <p className="italic text-on-surface-variant/80">
            "La educación es el encendido de una llama, no el llenado de un recipiente."
          </p>
        </section>
      </main>

      <BottomNav />
    </div>
  );
}