import { FormEvent, useState } from "react";
import { Show, SignInButton, UserButton, useAuth } from "@clerk/react";

type ApiResponse = {
  summary?: string;
  detail?: string;
};

const MINIMUM_TEXT_LENGTH = 20;
const MAXIMUM_TEXT_LENGTH = 12_000;

function App() {
  const { getToken, isSignedIn } = useAuth();
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSummary("");
    setError("");

    if (text.trim().length < MINIMUM_TEXT_LENGTH) {
      setError(`Escribe al menos ${MINIMUM_TEXT_LENGTH} caracteres.`);
      return;
    }

    if (!isSignedIn) {
      setError("Debes iniciar sesión.");
      return;
    }

    setIsLoading(true);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Tu sesión ha caducado. Inicia sesión de nuevo.");
      }

      // La ruta relativa funciona en local y en el mismo proyecto Serverless de Vercel.
      const response = await fetch("/api/summarize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ text }),
      });

      const data = (await response.json().catch(() => ({}))) as ApiResponse;

      if (!response.ok) {
        throw new Error(data.detail ?? "No se pudo generar el resumen.");
      }

      setSummary(data.summary ?? "El backend no devolvió ningún resumen.");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Ha ocurrido un error inesperado.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-10 text-slate-900 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <header className="mb-8">
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.25em] text-indigo-600">
            Resumia
          </p>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Resume textos con IA
          </h1>
          <p className="mt-3 max-w-2xl text-lg text-slate-600">
            Pega un texto y obtén un resumen breve y claro.
          </p>
          <div className="mt-4">
            <Show when="signed-out">
              <SignInButton mode="modal">
                <button className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white">
                  Iniciar sesión
                </button>
              </SignInButton>
            </Show>
            <Show when="signed-in">
              <UserButton />
            </Show>
          </div>
        </header>

        <Show when="signed-out">
          <p>Inicia sesión para generar un resumen.</p>
        </Show>
        <Show when="signed-in">
        <form onSubmit={handleSubmit} className="rounded-2xl bg-white p-5 shadow-sm sm:p-7">
          <label htmlFor="text" className="mb-2 block font-semibold">
            Texto para resumir
          </label>
          <textarea
            id="text"
            value={text}
            onChange={(event) => setText(event.target.value)}
            minLength={MINIMUM_TEXT_LENGTH}
            maxLength={MAXIMUM_TEXT_LENGTH}
            rows={10}
            required
            placeholder="Escribe o pega aquí el texto que quieres resumir..."
            className="w-full resize-y rounded-xl border border-slate-300 p-4 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
          />

          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-slate-500">
              {text.length} / {MAXIMUM_TEXT_LENGTH} caracteres
            </p>
            <button
              type="submit"
              disabled={isLoading}
              className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-wait disabled:opacity-60"
            >
              {isLoading ? "Resumiendo..." : "Generar resumen"}
            </button>
          </div>
        </form>
        </Show>

        {error && (
          <div role="alert" className="mt-6 rounded-xl bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        <Show when="signed-in">
          {summary && (
            <section className="mt-6 rounded-2xl bg-white p-5 shadow-sm sm:p-7" aria-live="polite">
              <h2 className="mb-3 text-xl font-bold">Resumen</h2>
              <p className="whitespace-pre-wrap leading-7 text-slate-700">{summary}</p>
            </section>
          )}
        </Show>
      </div>
    </main>
  );
}

export default App;
