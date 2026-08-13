# ventana.ia — Sistema

**02 // SYS.VENTANA**
Constraint → rewrite → advantage.

---

## 3. Estructura de producto y arquitectura

### Qué es

Una capa de control de vida útil colocada *sobre* el ERP de Súper Vivar, sin pedirle al ERP que cambie.

El documento de trabajo del depósito no es el remito del proveedor: es el **Reporte de Movimientos por Carátulas** que Logicom/Logex ya imprime al ingresar (producto + cantidad + FC). El ERP registra el qué y el cuánto. No registra el cuándo vence. ventana.ia lee esa carátula y pide solo la pieza que falta.

```
                    ┌──────────────────────┐
   foto carátula →  │  visión (Grok 4.6)   │
   (Logicom/Logex)  │  extracción líneas   │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │  revisión humana     │
                    │  + fecha vencimiento │
                    └──────────┬───────────┘
                               ▼
         ┌─────────────────────┴─────────────────────┐
         ▼                                           ▼
  SQLite  lotes / acciones / umbrales         Telegram
         ▼                                           ▼
  VENTANA://CONTROL                          señal escalonada
  retiro · promoción · cantidad
```

### Stack (y por qué)

| Capa | Elección | Motivo |
|---|---|---|
| Superficie | FastAPI + Jinja2 + CSS propio | Craft Runa + mobile-first real. Streamlit no puede. |
| Datos | SQLite (WAL) | Cero ops. Migrable a Postgres sin reescribir dominio. |
| Visión | SpaceXAI / Grok 4.6 (`XAI_API_KEY`) | Documento + imagen en un solo modelo. Sin Paddle + LLM en el depósito. |
| Alertas | Telegram Bot API | El canal que el encargado ya tiene abierto. |
| Jobs | APScheduler in-process | Digest diario + tick de críticos. Sin Redis. |
| Auth | sesión firmada + PBKDF2 | Dos roles. Sin IdP. |

Fallback: si no hay `XAI_API_KEY`, la captura sigue viva. Se carga la foto (o no) y las líneas se escriben a mano. El sistema nunca depende de la IA para existir.

### Árbol

```
ventana.ia/
├── run.py                  arranque
├── schema.sql              fuente de verdad del modelo
├── requirements.txt
├── .env.example
├── DIRECCION.md            naming + arte
├── SISTEMA.md              este documento
├── README.md
├── ventana/
│   ├── config.py
│   ├── db.py
│   ├── auth.py
│   ├── risk.py
│   ├── vision.py
│   ├── alerts.py
│   ├── seed.py
│   └── web.py              rutas + app
├── templates/
└── static/
    ├── css/system.css
    ├── js/system.js
    ├── img/mark.svg
    └── manifest.json
```

### Roles

| Rol | Puede |
|---|---|
| `deposito` | Capturar, revisar, confirmar, retirar, promoción, editar cantidad, ver control e historial |
| `admin` | Todo lo anterior + productos, protocolo (umbrales, Telegram), usuarios |

### Decisiones de dominio

- Un **ingreso** (intake) es un remito leído. Puede quedar en `borrador` hasta que alguien asigne vencimientos y confirme.
- Un **lote** (batch) nace al confirmar. Es la unidad de control. Tiene cantidad viva, vencimiento y estado operativo.
- El **riesgo** no se guarda: se deriva de `expires_at` vs. hoy vs. umbrales. Los umbrales son protocolo, no código.
- `promocion` es un estado operativo *y* sigue teniendo riesgo. Un lote puede estar EN PROMOCIÓN y CRÍTICO a la vez.
- Retirar no borra. Escribe una acción y saca el lote de circulación.
- Poner cantidad en 0 cierra el lote como `agotado`.

---

## 6. Schema

Fuente ejecutable: `schema.sql`.

```
users            operador del sistema
products         catálogo mínimo (SKU Vivar cuando existe)
intakes          foto + metadatos del remito
intake_lines     líneas editables pre-confirmación
batches          lotes vivos / cerrados
actions          historial inmutable de movimientos
settings         protocolo (umbrales, telegram, nombre)
alert_log        deduplicación de señales
```

Relación central:

```
products 1 ─── * batches
intakes  1 ─── * intake_lines
intakes  1 ─── * batches
users    1 ─── * intakes, batches, actions
```

Índices en `expires_at`, `status`, `product_id`, `actions(batch_id, created_at)`.

Migración futura a Postgres: el SQL es ANSI de propósito. Cambiar el conector en `db.py`. No hay tipos SQLite-only más que `INTEGER` booleanos.

---

## 7. Flujo de usuario — de la foto a la alerta

**Escenario.** Llega un palet. El remito viene en la mano. Son las 07:50. El operario no se sienta.

1. **Abre ventana.ia** en el celular (PWA / Safari / Chrome). Login `deposito`.
2. Toca **CAPTURAR**. El kicker dice `01 // CAPTURA DE INGRESO`.
3. Toca el frame. Se abre la cámara trasera (`capture=environment`). Dispara a la **carátula** (Reporte de Movimientos) sobre la mesa. También sirve un remito de proveedor.
4. Toca **ACTIVAR LECTURA**. Scan line. Grok 4.6 recibe la imagen (lado máximo 2048, JPEG).
5. El modelo reconoce carátula Logicom/Logex: número de carátula, FC, operador, líneas. Ignora RSC/VTA y el total. Suma ajustes negativos del mismo producto (ej. Topline +24 y −12 → 12). Match contra el catálogo Vivar.
6. Cae en **REVISIÓN**. El operario corrige una cantidad, borra una línea de IVA que se coló, toca `+15` en “aplicar a todas” porque este proveedor es lácteo de quincena. Ajusta dos líneas que vencen antes.
7. Toca **CONFIRMAR INGRESO**. Flash rune. Nacen los lotes. Copy: `Ingreso activado.`
8. En **CONTROL**, esos lotes aparecen en la tira (preventivo / estable / el que corresponda).
9. Los días pasan. El scheduler evalúa umbrales.
   - Preventivo: entra a la tira. No molesta por Telegram (salvo digest).
   - Advertencia: digest diario a las 08:00 al chat del encargado.
   - Crítico o vencido: señal inmediata, una vez por lote por nivel por día.
10. El encargado abre el lote y toca **ACTIVAR PROMOCIÓN** o **RETIRAR DE CIRCULACIÓN**. Queda escrito en historial: quién, cuándo, cuánto.

Sin foto: `cargar sin foto` → mismo flujo, líneas vacías, se escribe a mano. El rewrite no se rompe si la visión no está.

---

## 8. Fase 2

La fase 1 libera la ventaja: ver la ventana y actuar. La fase 2 la ensancha.

### Integraciones

- **Logicom / ERP Vivar.** Alta de ingreso automática desde el movimiento interno, sin foto, cuando el documento ya existe digital. La foto queda como fallback y como auditoría.
- **Catálogo SYS.COMMERCE.** Importar SKU + nombre + rubro desde `products.json` de Súper Vivar. Un producto, dos sistemas.
- **WhatsApp Business** como canal gemelo de Telegram (encargados que no quieren otro bot).
- **Impresión de etiqueta de lote** (SKU + vencimiento + código corto) para la estantería. El ERP no etiqueta: nosotros sí.

### Craft

- Calibración de visión con remitos reales de los proveedores de Vivar (La Paulina, Tregar, fiambrería, verdura). Hoy el prompt es general; con 20 remitos se vuelve preciso.
- Match de producto por embedding + SKU de barras si la foto incluye el código.
- Modo “cámara viva” (getUserMedia) sin pasar por el rollo.
- Resumen semanal de merma evitada: kilos/unidades retiradas a tiempo vs. vencidas en góndola.

### Extensiones de sistema (misma práctica, otra ranura)

- **ventana.ia / góndola** — el repositor recorre y marca “visto / no está”. Cierra el loop depósito–sala.
- **ventana.ia / comercial** — los lotes en advertencia generan una lista de precios de quema lista para cartel y para SYS.COMMERCE.
- **SYS.MERMA** — si algún día el número lo pide: costo de lo retirado, causa, proveedor. No antes.

No se agrega un módulo porque “queda lindo”. Se agrega cuando identifica una restricción que esta ranura todavía no corta.
