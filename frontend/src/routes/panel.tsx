import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { BottomNav } from "@/components/BottomNav";
import { Icon } from "@/components/Icon";

export const Route = createFileRoute("/panel")({
  head: () => ({
    meta: [
      { title: "Faro UNRaf — Panel de profesores" },
      {
        name: "description",
        content:
          "Monitoreá el progreso y nivel de confianza de tus estudiantes en tiempo real.",
      },
      { property: "og:title", content: "Faro UNRaf — Panel" },
      {
        property: "og:description",
        content: "Insights anónimos de confianza académica por tema.",
      },
    ],
  }),
  component: TeacherPanel,
});

type Subject = "matematica" | "fisica" | "historia";

const DATA: Record<
  Subject,
  {
    label: string;
    score: number;
    students: number;
    distribution: [number, number, number]; // low, med, high (percent)
    topics: { title: string; desc: string; status: "warn" | "ok"; tag: string }[];
  }
> = {
  matematica: {
    label: "Matemática",
    score: 68,
    students: 35,
    distribution: [12, 55, 33],
    topics: [
      {
        title: "Cálculo Integral",
        desc: "Bajo nivel de confianza reportado (42/100)",
        status: "warn",
        tag: "+8 respuestas",
      },
      {
        title: "Derivadas y Límites",
        desc: "Confianza estable en la mayoría del grupo (74/100)",
        status: "ok",
        tag: "+22 respuestas",
      },
    ],
  },
  fisica: {
    label: "Física",
    score: 54,
    students: 28,
    distribution: [30, 50, 20],
    topics: [
      {
        title: "Termodinámica",
        desc: "Confianza media baja (48/100)",
        status: "warn",
        tag: "+11 respuestas",
      },
      {
        title: "Cinemática",
        desc: "Confianza estable (70/100)",
        status: "ok",
        tag: "+17 respuestas",
      },
    ],
  },
  historia: {
    label: "Historia",
    score: 82,
    students: 41,
    distribution: [8, 32, 60],
    topics: [
      {
        title: "Revolución Industrial",
        desc: "Confianza alta (84/100)",
        status: "ok",
        tag: "+25 respuestas",
      },
      {
        title: "Edad Media",
        desc: "Confianza estable (78/100)",
        status: "ok",
        tag: "+16 respuestas",
      },
    ],
  },
};

function TeacherPanel() {
  const [subject, setSubject] = useState<Subject>("matematica");
  const d = DATA[subject];
  const maxBar = useMemo(() => Math.max(...d.distribution), [d.distribution]);

  return (
    <div className="min-h-screen bg-surface pb-32 md:pb-12">
      <AppHeader />

      <main className="pt-24 px-4 md:px-20 max-w-[1280px] mx-auto">
        {/* Header */}
        <section className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-primary tracking-tight mb-2">
              Panel de Profesores
            </h1>
            <p className="text-on-surface-variant max-w-xl">
              Monitoreá el progreso y nivel de confianza de tus estudiantes en
              tiempo real.
            </p>
          </div>
          <div className="relative w-full md:w-64">
            <label
              htmlFor="subject"
              className="block text-[13px] font-semibold tracking-wide text-primary mb-2"
            >
              Filtrar por Tema
            </label>
            <select
              id="subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value as Subject)}
              className="w-full bg-surface-container-lowest border border-outline-variant rounded-xl px-4 py-3 text-on-surface focus:ring-2 focus:ring-secondary focus:border-secondary outline-none appearance-none cursor-pointer transition-all"
            >
              <option value="matematica">Matemática</option>
              <option value="fisica">Física</option>
              <option value="historia">Historia</option>
            </select>
            <Icon
              name="expand_more"
              className="absolute right-3 bottom-3 pointer-events-none text-on-surface-variant"
            />
          </div>
        </section>

        {/* Bento */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-12">
          {/* Confidence avg */}
          <div className="md:col-span-4 relative overflow-hidden bg-surface-container-lowest p-6 rounded-2xl border border-outline-variant/60 card-shadow flex flex-col justify-between group">
            <div className="z-10 relative">
              <Icon
                name="insights"
                filled
                className="text-secondary text-[32px] mb-3"
              />
              <h3 className="text-[12px] font-semibold tracking-[0.12em] text-on-surface-variant uppercase mb-1">
                Promedio de Confianza
              </h3>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl md:text-6xl font-extrabold text-primary tracking-tight">
                  {d.score}
                </span>
                <span className="text-2xl font-bold text-on-surface-variant">
                  /100
                </span>
              </div>
            </div>
            <div className="mt-8 z-10 relative">
              <div className="w-full bg-surface-container h-2 rounded-full overflow-hidden">
                <div
                  className="bg-secondary h-full rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${d.score}%` }}
                />
              </div>
              <p className="text-[13px] font-semibold text-secondary mt-2 flex items-center gap-1">
                <Icon name="trending_up" className="text-[16px]" />
                +5% desde la semana pasada
              </p>
            </div>
            <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-secondary-fixed/30 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700" />
          </div>

          {/* Students */}
          <div className="md:col-span-3 bg-primary text-on-primary p-6 rounded-2xl card-shadow flex flex-col justify-center items-center text-center relative overflow-hidden">
            <Icon
              name="groups"
              filled
              className="absolute -left-2 -top-2 text-white/10 text-[160px] pointer-events-none select-none"
            />
            <div className="z-10">
              <span className="text-5xl md:text-6xl font-extrabold tracking-tight">
                {d.students}
              </span>
              <h3 className="text-xl font-bold mt-1">Estudiantes</h3>
              <p className="opacity-80 mt-1 text-sm">
                respondieron la encuesta
              </p>
            </div>
            <button className="mt-5 z-10 px-4 py-2 bg-on-primary text-primary text-[13px] font-bold rounded-lg hover:bg-surface-variant transition-colors">
              Ver Detalles
            </button>
          </div>

          {/* Distribution */}
          <div className="md:col-span-5 bg-surface-container-lowest p-6 rounded-2xl border border-outline-variant/60 card-shadow">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-primary">
                Distribución de Confianza
              </h3>
              <button
                className="text-on-surface-variant hover:text-primary transition-colors"
                aria-label="Información"
              >
                <Icon name="info" />
              </button>
            </div>
            <div className="flex items-end justify-around h-48 gap-4 px-2">
              {[
                {
                  label: "Bajo",
                  value: d.distribution[0],
                  cls: "bg-error-container",
                },
                {
                  label: "Medio",
                  value: d.distribution[1],
                  cls: "bg-secondary-container",
                },
                {
                  label: "Alto",
                  value: d.distribution[2],
                  cls: "bg-secondary",
                },
              ].map((b) => (
                <div
                  key={b.label}
                  className="flex flex-col items-center flex-1 h-full"
                >
                  <div className="text-[13px] font-semibold text-on-surface-variant mb-2">
                    {b.value}%
                  </div>
                  <div className="flex-1 w-full flex items-end">
                    <div
                      className={`${b.cls} w-full rounded-t-lg transition-[height] duration-1000 ease-out`}
                      style={{ height: `${(b.value / maxBar) * 100}%` }}
                    />
                  </div>
                  <div className="mt-3 text-[13px] font-semibold text-on-surface-variant">
                    {b.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Critical topics */}
        <section>
          <h2 className="text-2xl font-bold text-primary mb-6">
            Temas Críticos en {d.label}
          </h2>
          <div className="space-y-3">
            {d.topics.map((t) => (
              <div
                key={t.title}
                className="bg-surface-container-lowest p-4 rounded-xl border border-outline-variant/60 hover:bg-surface-container-low transition-colors flex items-center gap-4"
              >
                <div
                  className={
                    "w-12 h-12 rounded-full grid place-items-center shrink-0 " +
                    (t.status === "warn"
                      ? "bg-error-container text-error"
                      : "bg-secondary-fixed text-secondary")
                  }
                >
                  <Icon name={t.status === "warn" ? "warning" : "check_circle"} />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-bold text-primary truncate">{t.title}</h4>
                  <p className="text-on-surface-variant text-sm">{t.desc}</p>
                </div>
                <div className="hidden md:flex items-center gap-3">
                  <span className="px-3 py-1 rounded-full bg-secondary-container/60 text-on-secondary-container text-[12px] font-bold tracking-wide">
                    {t.tag}
                  </span>
                </div>
                <button className="text-secondary text-[13px] font-bold hover:underline shrink-0">
                  Ver Respuestas
                </button>
              </div>
            ))}
          </div>
        </section>
      </main>

      <BottomNav />
    </div>
  );
}