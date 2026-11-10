export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const isChat = url.pathname === "/api/chat";
    const isStatus = url.pathname === "/api/status";

    if (isChat || isStatus) {
      if (!env.DEXBOT_ORIGIN) {
        return Response.json(
          { error: "DEXBOT_ORIGIN não foi configurado no Worker." },
          { status: 503, headers: { "Cache-Control": "no-store" } }
        );
      }
      if ((isChat && request.method !== "POST") || (isStatus && request.method !== "GET")) {
        return Response.json({ error: "Método não permitido." }, { status: 405 });
      }

      let origin;
      try {
        origin = new URL(env.DEXBOT_ORIGIN);
        if (origin.protocol !== "https:") throw new Error("HTTPS obrigatório");
      } catch {
        return Response.json({ error: "DEXBOT_ORIGIN precisa ser uma URL HTTPS válida." }, { status: 500 });
      }

      const target = new URL(url.pathname, origin);
      const headers = new Headers({ "Accept": "application/json" });
      let body;
      if (isChat) {
        headers.set("Content-Type", "application/json");
        body = await request.text();
        if (body.length > 100000) {
          return Response.json({ error: "Mensagem muito grande." }, { status: 413 });
        }
      }

      try {
        const upstream = await fetch(target, {
          method: request.method,
          headers,
          body,
          signal: AbortSignal.timeout(120000)
        });
        return new Response(upstream.body, {
          status: upstream.status,
          headers: {
            "Content-Type": upstream.headers.get("Content-Type") || "application/json; charset=utf-8",
            "Cache-Control": "no-store"
          }
        });
      } catch {
        return Response.json(
          { error: "O túnel até o PC está offline. Inicie o Dexbot e o cloudflared." },
          { status: 502, headers: { "Cache-Control": "no-store" } }
        );
      }
    }

    if (!env.ASSETS) {
      return new Response("Arquivos do site não foram configurados no Worker.", { status: 500 });
    }
    return env.ASSETS.fetch(request);
  }
};
