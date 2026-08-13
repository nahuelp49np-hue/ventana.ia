# ventana.ia

**02 // SYS.VENTANA**
Control de vida útil de Súper Vivar. Hecho por Runa.

> Identify the constraint → rewrite the rule → release the advantage.

El ERP no rastrea vencimiento por lote. ventana.ia no le pide permiso: se coloca encima. El depósito saca una foto del remito, la visión arma las líneas, el operario asigna la fecha, el negocio actúa antes de que la merma sea un hecho.

Documentos de sistema:
- [DIRECCION.md](DIRECCION.md) — naming visual y dirección de arte
- [SISTEMA.md](SISTEMA.md) — arquitectura, schema, flujo, fase 2
- [schema.sql](schema.sql) — modelo de datos

---

## Por qué no es Streamlit

El depósito entra con el celular, con las manos ocupadas, en siete segundos. Streamlit impone chrome de desktop. Esta activación necesita control de cada hairline (void / bone / rune) y captura nativa de cámara.

**Python se queda donde aporta:** visión, SQLite, Telegram, umbrales.
**La superficie es propia:** FastAPI + HTML/CSS del sistema Runa.

---

## Requisitos

- Python 3.11 o 3.12
- Un celular en la misma red (depósito)
- Opcional: clave SpaceXAI (`XAI_API_KEY`) para leer remitos
- Opcional: bot de Telegram para alertas

Sin clave de visión el sistema **igual funciona**: se carga el remito y las líneas se escriben a mano.

---

## Instalación (Windows)

Abrí PowerShell:

```powershell
cd $env:USERPROFILE\ventana.ia
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Editá `.env` si vas a usar visión o querés un `SECRET_KEY` de producción.

```powershell
python run.py
```

O, si el entorno ya está creado (está), doble click en `activar.bat`.

El sistema queda en:

```
http://127.0.0.1:5202
```

Desde el celular, en la misma Wi-Fi:

```
http://<IP-de-esta-PC>:5202
```

La IP local se ve con `ipconfig` (IPv4). El firewall de Windows tiene que dejar pasar el puerto **5202**.

---

## Accesos de activación

| Usuario    | Clave  | Rol      |
|------------|--------|----------|
| `deposito` | `vivar`| depósito |
| `admin`    | `runa` | admin    |

Cámbialos en producción (Protocolo no cambia claves; creá un admin nuevo en Operadores y dejá de usar estos).

La base nace con lotes de demostración del catálogo real de Súper Vivar (Tregar, La Paulina, fiambrería, carnicería) cubriendo crítico / advertencia / preventivo / estable / promoción / retiro.

---

## Visión (foto del remito)

1. Creá una clave en [console.x.ai](https://console.x.ai)
2. En `.env`: `XAI_API_KEY=xai-...`
3. Reiniciá. En Captura, el kicker pasa a leer el documento con **Grok 4.6**.

Modelos y endpoint: `https://api.x.ai/v1` · `grok-4.6`.

Si más adelante querés calibrar la lectura, mandá remitos reales de los proveedores de Vivar. El prompt ya ignora IVA, CAE y totales; con 20 documentos del territorio se vuelve preciso.

---

## Telegram

1. Hablá con [@BotFather](https://t.me/BotFather), creá un bot, copiá el token.
2. Escribile al bot desde el chat del encargado (o un grupo).
3. El `chat_id` se obtiene hablando con `@userinfobot` o mirando `getUpdates`.
4. Entrá como **admin** → Protocolo. Pegá token y chat, activá alertas, mandá una señal de prueba.

Comportamiento:
- **Crítico / vencido:** cada 15 minutos, una vez por lote por nivel por día.
- **Digest:** a la hora configurada (08:00 por defecto), recorre advertencia (y preventivo si se marca).

---

## Uso mínimo

1. Login depósito.
2. **Capturar** → foto del remito → Activar lectura.
3. Revisar líneas, asignar vencimiento (`+7 / +15 / +30` o fecha).
4. **Confirmar ingreso.**
5. En **Control**, actuar: retirar o promoción.
6. **Historial** guarda quién, cuándo, cuánto.

---

## Datos

- Base: `data/ventana.db` (SQLite, WAL)
- Fotos: `data/uploads/`
- Schema: `schema.sql`

Para arrancar de cero, cerrá el proceso y borra `data/ventana.db`.

---

## Puerto y red

`HOST=0.0.0.0` y `PORT=5202` en `.env`.
`5202` es el índice de esta activación (02) sobre Vivar.

---

hecho por RUNA · Súper Vivar · SYS.VENTANA
