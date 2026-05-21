import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { BottomNav } from "@/components/BottomNav";
import { useLti } from "@/lib/lti-context";

// Librerías para procesar el texto con fórmulas matemáticas que devuelve tu API
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css"; // Estilos para renderizar LaTeX

// 1. Estructura idéntica al JSON que te devolvió la URL (image_8e53cc.png)
interface ChatLogAlumno {
  id: number;
  user_id: string;
  course_id: string;
  role: string;
  subtema: string;
  pregunta_original: string; // Coincide con tu Backend
  respuesta_bot: string;      // Coincide con tu Backend
  timestamp: string;
}

export const Route = createFileRoute("/visualizarfeedback")({
  component: VisualizarLogsAlumnos,
});

function VisualizarLogsAlumnos() {
  const { user } = useLti(); 
  const [logs, setLogs] = useState<ChatLogAlumno[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const cargarLogsAlumnos = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const baseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8080";
      // Si el entorno LTI no provee email todavía, usamos el tuyo por defecto para las pruebas
      const emailDocente = user?.email || "profesor@unraf.edu.ar"; 
      
      const response = await fetch(
        `${baseUrl}/api/logs-maestros?email_profesor=${encodeURIComponent(emailDocente)}`
      );

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error("Acceso denegado: Este email no figura como profesor autorizado.");
        }
        throw new Error(`Error del servidor backend: ${response.status}`);
      }

      const data = await response.json();
      setLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error de conexión con el backend");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarLogsAlumnos();
  }, [user?.email]);

  return (
    <div className="min-h-screen bg-slate-50 pb-24">
      <AppHeader anonymousId="Docente" />

      <main className="pt-24 px-4 md:px-12 max-w-4xl mx-auto flex flex-col gap-6 font-sans">
        
        {/* Fila del Título */}
        <div className="flex justify-between items-center border-b border-slate-200 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Panel de Monitoreo Áulico</h1>
            <p className="text-sm text-slate-500">Historial de interacciones y consultas de alumnos</p>
          </div>
          <button 
            onClick={cargarLogsAlumnos}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold transition-all shadow-md active:scale-95"
          >
            🔄 Actualizar Datos
          </button>
        </div>

        {/* Tarjeta de métricas */}
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm max-w-xs">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Consultas Registradas</span>
          <span className="text-3xl font-black text-slate-800 block mt-1">{logs.length}</span>
        </div>

        {/* Controladores de Estado */}
        {loading && <div className="text-center p-12 text-slate-400 italic">Leyendo logs_pedagogicos.db...</div>}
        {error && <div className="text-center p-6 bg-red-50 text-red-600 border border-red-200 rounded-xl font-bold">{error}</div>}

        {/* Despliegue de los Logs */}
        {!loading && !error && (
          <div className="flex flex-col gap-4">
            {logs.length === 0 ? (
              <div className="text-center p-12 bg-white border border-slate-200 rounded-xl text-slate-400 italic">
                No se encontraron chats guardados en la tabla de logs.
              </div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col gap-3">
                  
                  {/* Encabezado del log */}
                  <div className="flex justify-between items-center border-b border-slate-100 pb-2 text-xs text-slate-400 font-medium">
                    <span>Eje Temático: <strong className="text-indigo-600 uppercase">{log.subtema || "General"}</strong></span>
                    <span>{log.timestamp ? new Date(log.timestamp).toLocaleString("es-AR") : "Sin fecha"}</span>
                  </div>

                  {/* Bloques de contenido */}
                  <div className="grid grid-cols-1 gap-4 text-sm">
                    {/* Tarjeta de la Pregunta */}
                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                      <span className="font-bold text-xs text-blue-600 block mb-1">PREGUNTA DEL ESTUDIANTE:</span>
                      <p className="text-slate-800 font-medium">{log.pregunta_original}</p>
                    </div>

                    {/* Tarjeta de la Respuesta del Bot (Con soporte Markdown/LaTeX) */}
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 prose prose-slate max-w-none">
                      <span className="font-bold text-xs text-emerald-600 block mb-2">RESPUESTA DEL BOT:</span>
                      <div className="text-slate-700 leading-relaxed overflow-x-auto">
                        <ReactMarkdown 
                          remarkPlugins={[remarkMath]} 
                          rehypePlugins={[rehypeKatex]}
                        >
                          {log.respuesta_bot}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>

                </div>
              ))
            )}
          </div>
        )}
      </main>
      <BottomNav />
    </div>
  );
}