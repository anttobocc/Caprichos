# Asistente de Capricho con n8n + IA (Groq)

Chat flotante en el sitio que responde consultas de clientes (productos,
precios, envíos, anticipación, cómo pedir) usando un workflow de n8n con
un agente de IA.

## Cómo funciona

```
Navegador (chat del sitio)
   │  POST {"pregunta": "...", "sessionId": "..."}
   ▼
n8n  Webhook ─► HTTP Request "Catálogo Capricho" ─► AI Agent ─► Respond to Webhook
                  (GET /asistente/catalogo.json)     │  ├─ Groq Chat Model (openai/gpt-oss-120b)
                                                     │  └─ Simple Memory (sessionId, 5 mensajes)
   ◄──────────────────────────────── {"respuesta": "..."}
```

- **`/asistente/catalogo.json`** (Django) devuelve los productos activos,
  precios, combos y reglas del negocio tal como están en el panel. n8n lo
  lee en cada mensaje, así que si cambiás un precio en el panel el
  asistente lo sabe a los pocos minutos (caché de 5 min). No hay que
  tocar el workflow.
- La **memoria** usa el `sessionId` que genera el navegador (dura lo que
  la pestaña), así el cliente puede cambiar de tema y volver sin repetir.
- Si n8n no responde, el chat muestra un mensaje con el link de WhatsApp.

## Puesta en marcha

1. **API key de Groq**: crearla en https://console.groq.com/keys (no la
   compartas ni la subas al repo).
2. **Importar el workflow** en n8n: *Workflows → Import from File →*
   `capricho_asistente.json`.
3. Abrir el nodo **Groq Chat Model** → *Credential* → crear una con la API
   key. Modelo: `openai/gpt-oss-120b` (Groq dio de baja
   `llama-3.3-70b-versatile` en agosto de 2026; si en el futuro cambia,
   elegí otro de la lista del nodo).
4. Si probás contra tu compu, en **Catálogo Capricho** cambiá la URL por
   una pública (n8n cloud no ve `127.0.0.1`).
5. **Publicar / activar** el workflow y copiar la **Production URL** del
   nodo Webhook (termina en `/webhook/capricho-asistente`, sin `-test`).
6. En PythonAnywhere, agregar al `.env` del servidor
   (`/home/capricho/Caprichos/.env`):

   ```
   N8N_CHAT_WEBHOOK_URL=https://TU-CUENTA.app.n8n.cloud/webhook/capricho-asistente
   ```

   y recargar la web app (*Web → Reload*). Sin esa variable el chat no se
   muestra.

### CORS

El nodo Webhook tiene en *Options → Allowed Origins* los dominios que
pueden llamar al chat (`https://capricho.pythonanywhere.com` y localhost
para pruebas). Si cambiás de dominio, agregalo ahí.

### Probar desde PowerShell

```powershell
$body = @{ pregunta = "¿Qué empanadas tienen?"; sessionId = "prueba-1" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://TU-CUENTA.app.n8n.cloud/webhook/capricho-asistente" `
  -Method Post -ContentType "application/json" -Body $body
```

Cuidá los créditos/límites de Groq y de las ejecuciones de n8n cuando
pruebes con muchas preguntas.
