export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/chat" || url.pathname === "/api/status") {
      if (!env.DEXBOT_ORIGIN || !env.DEXBOT_TOKEN) {
        return Response.json({
          error: "O Worker ainda não foi configurado. Defina DEXBOT_ORIGIN e DEXBOT_TOKEN."
        }, { status: 503, headers: { "Cache-Control": "no-store" } });
      }

      if (url.pathname === "/api/chat" && request.method !== "POST") {
        return Response.json({ error: "Método não permitido" }, { status: 405 });
      }
      if (url.pathname === "/api/status" && request.method !== "GET") {
        return Response.json({ error: "Método não permitido" }, { status: 405 });
      }

      let origin;
      try {
        origin = new URL(env.DEXBOT_ORIGIN);
        if (origin.protocol !== "https:") throw new Error("HTTPS obrigatório");
      } catch {
        return Response.json({ error: "DEXBOT_ORIGIN precisa ser uma URL HTTPS válida." }, { status: 500 });
      }

      const upstreamUrl = new URL(url.pathname, origin);
      const headers = new Headers({
        "Authorization": "Bearer " + env.DEXBOT_TOKEN,
        "Accept": "application/json"
      });
      if (request.method === "POST") {
        headers.set("Content-Type", "application/json");
      }

      try {
        const upstream = await fetch(upstreamUrl, {
          method: request.method,
          headers,
          body: request.method === "POST" ? await request.text() : undefined,
          signal: AbortSignal.timeout(120000)
        });
        return new Response(upstream.body, {
          status: upstream.status,
          headers: {
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": "no-store"
          }
        });
      } catch {
        return Response.json({
          error: "Não consegui alcançar o Dexbot no PC. Confira se o servidor e o túnel estão ligados."
        }, { status: 502, headers: { "Cache-Control": "no-store" } });
      }
    }

    return env.ASSETS.fetch(request);
  }
};
