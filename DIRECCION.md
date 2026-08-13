# ventana.ia — Naming visual y dirección de arte

**02 // SYS.VENTANA**
Hecho por Runa. Operado por Súper Vivar.
Una runa no explica. Activa.

---

## 0. Constraint → rewrite → advantage

**Constraint.** El ERP no etiqueta ni rastrea vencimiento por lote/ingreso. El depósito no tiene herramienta. La merma es silenciosa. La góndola se entera tarde.

**Rewrite.** La foto del remito *es* el ingreso. La ventana de vida útil se declara en el momento en que la mercadería toca el depósito. El sistema no pide que el ERP cambie: se coloca encima.

**Advantage.** El negocio ve la ventana *antes* de que se cierre. Retiro, promoción o reposición dejan de ser descubrimiento y pasan a ser protocolo.

---

## 1. Naming visual

### El nombre

**ventana.ia**

No es un acrónimo. No es un slogan. Es una dirección de sistema.

| Capa | Forma | Función |
|---|---|---|
| Palabra | `ventana` | La vida útil restante. El hueco de tiempo que todavía se puede usar. |
| Apertura | `.` | El corte. El vidrio. El punto donde se mira. |
| Inteligencia | `ia` | Quien lee el remito cuando el operario no puede (ni debe) tipear. |
| Código | `SYS.VENTANA` | Cómo se archiva junto a `SYS.COMMERCE`. |
| Índice | `02` | Segunda activación sobre Súper Vivar. |

Se escribe **siempre en minúsculas**: `ventana.ia`.
Se dice: *ventana punto i a*.
No se dice “Ventana IA”, ni “VentanaIA”, ni “la app de vencimientos”.

### Por qué este nombre y no otro

- **Vencimiento** nombra el final. **Ventana** nombra el tiempo que todavía existe. El producto actúa sobre lo abierto, no sobre el cadáver.
- El punto no es decoración tipográfica. Es la ranura. Es lo que diferencia a este sistema de un dashboard: una apertura de control.
- `.ia` lo ancla a una época y a un método (visión + extracción), sin vender “AI-powered” como adjetivo de agencia.
- Convive con Runa: Runa nombra la práctica; ventana.ia nombra el dispositivo colocado sobre el depósito.

### Lockup

```
        ⌬          hexágono Runa, ranura vertical adentro
   ventana.ia      Instrument Serif + mono en .ia
 SYS.VENTANA  ·  02
 SÚPER VIVAR       firma de operación, no de autoría
```

**Jerarquía de firma**
1. ventana.ia — el dispositivo
2. RUNA — el sello (discreto, siempre presente)
3. Súper Vivar — el cuerpo sobre el que opera

Nunca el logo de Vivar como hero. Nunca Runa como splash corporativo.
El sello Runa vive en el pie, en el login y en el favicon. Se siente, no se grita.

### Código de sistema (uso en UI)

```
SYS.VENTANA
VENTANA://CONTROL
VENTANA://CAPTURA
VENTANA://PROTOCOLO
02  //  CONTROL DE VIDA ÚTIL
RUNA.ACTIVATE  SYS://VENTANA
```

### El isotipo — la ranura

El mark de Runa es un hexágono de punta, un tallo y un punto.
El mark de ventana.ia hereda el hexágono (pertenece a la misma práctica) y **reescribe el interior**: el tallo + punto se convierten en una **ranura vertical**. Una ventana. Un diafragma.

La ranura cambia de color según el estado del sistema (no según un theme):

| Estado | Color de ranura |
|---|---|
| En calma | `#B7A48A` rune |
| Preventivo | `#8FA37A` |
| Advertencia | `#D4B06A` |
| Crítico / vencido | `#E07A72` |

El hexágono nunca cambia. Cambia lo que se ve a través de él.

Still de mood del isotipo: `static/img/mood.jpg` — void, hexágono, ranura. Sin letra. El objeto, no el slogan.

---

## 2. Mood

No es una app de startup. No es un panel de Streamlit. No es un Excel con CSS.

Es una **herramienta de depósito que parece un instrumento**.
Referencias de sensación, no de copia:

- Terminal militar de inventario, despojada de camuflaje
- Reloj de buceo: una sola aguja que importa, el resto es bisel
- Mesa de corte de fiambres a las 07:40: luz fea, decisiones rápidas
- El sitio de Runa: void, bone, rune, mono, ranuras, silencio

**Adjetivos que sí:** preciso, denso, caro, seco, accionable, territorial.
**Adjetivos que no:** friendly, smart, playful, corporativo, “intuitivo”, neón, glassmorphism de Dribbble.

El operario tiene las manos ocupadas, la luz del depósito es irregular y no va a leer un párrafo. Cada pantalla responde una sola pregunta:

1. Login — ¿quién entra al sistema?
2. Control — ¿qué se vence y qué hago?
3. Captura — ¿dónde pongo el remito?
4. Revisión — ¿está bien lo que leyó, cuándo vence?
5. Lote — ¿retiro, promuevo o corrijo?
6. Historial — ¿qué ya salió de circulación?
7. Protocolo — ¿cuándo avisa, a quién?

---

## 3. Color system

Hereda Runa. Extiende solo lo que el depósito necesita: urgencia.

```
VOID        #0A0A0A    fondo primario
VOID-2      #111111    superficie
VOID-3      #181816    superficie elevada / input
BONE        #EDE8DF    texto primario
BONE-DIM    #8F8A81    texto secundario
RUNE        #B7A48A    acento de sistema, firma, .ia
SYSTEM      #6E7A72    estable / ok / meta
LINE        rgba(237,232,223,0.10)
```

**Urgencia — color coding intencional**

```
VENCIDO       #8A3530 fondo    #F2ECE4 texto    ya no hay ventana
CRÍTICO       #E07A72          ≤ umbral crítico (default 2 días)
ADVERTENCIA   #D4B06A          ≤ umbral advertencia (default 7)
PREVENTIVO    #8FA37A          ≤ umbral preventivo (default 15)
ESTABLE       #6E7A72          fuera de umbral
PROMOCIÓN     #B7A48A          acción comercial activa
RETIRADO      #5C5852          fuera de circulación
```

Reglas:
- El color nunca es el único canal. Siempre hay palabra: `CRÍTICO`, `1 DÍA`.
- No hay semáforo genérico (verde/amarillo/rojo de Bootstrap). Los tonos viven en la familia bone/rune: tierra, no UI kit.
- Superficies de alerta = el color al 12–16% sobre void. El texto del nivel va al 100%.
- En depósito, el contraste bone/void es el modo de alta visibilidad. No hay light mode en el MVP. La pantalla del celular se ilumina sola; el problema es la jerarquía, no el paper.

**Selección y foco**
```
::selection   rune / 30%
:focus        bone / 55%  outline 1px, offset 3px
```

---

## 4. Tipografía

| Rol | Familia | Uso |
|---|---|---|
| Display | **Instrument Serif** | Wordmark `ventana`, números de ventana restante, títulos de sección |
| Sans | **Geist** | Cuerpo, nombres de producto, botones |
| Mono | **Geist Mono** | Kickers, códigos, SKU, fechas `14.08`, cantidades, protocolos |

**Escala (mobile)**

```
kicker     10px  mono   uppercase  tracking 0.24em  bone-dim
wordmark   clamp(2.4rem, 12vw, 4.5rem)  display  tracking 0.08em
número     3.25rem display    la ventana (días)
ui         15–16px sans
meta       11–12px mono
botón      11px  sans/mono  uppercase  tracking 0.20em
```

Nunca fuentes decorativas. Nunca display en párrafos. El número de días es el único gesto “grande”: es el producto.

El `.ia` del wordmark se setea en mono, un grado más chico, color rune. El punto es rune.

---

## 5. Principios visuales

1. **Una pregunta por pantalla.** Si hay dos, hay dos pantallas.
2. **La ventana se ve.** El número de días no es un badge: es el sujeto.
3. **Esquinas de sistema.** Frames con ticks de 14px (lenguaje Runa). No rounded-card de SaaS. Radio máximo: 2px en chips, 999 en el botón de activar.
4. **Hairlines, no sombras.** Profundidad = borde `LINE` + un grado de void. Nada de drop-shadow violeta.
5. **Denso donde hay dato, generoso donde hay decisión.** Lista de lotes: compacta. Captura y confirmar: aire, un solo CTA.
6. **Tamaño de dedo.** Tap mínimo 48px. Steppers de cantidad enormes (guantes, frío, apuro).
7. **Mobile-first extremo.** El desktop es el mismo sistema ensanchado, no otro producto. Captura nunca se “desktopiza”.
8. **Microinteracción = activar / controlar.** Scan line al leer el remito. Flash rune al confirmar ingreso. Pulso lento en crítico. Nada rebota. Nada confetti.
9. **Ruido de sistema, no textura de marca.** Grain al 4.5%, grilla de 80px, scan casi invisible. Igual que runa-studio.
10. **El sello no compite.** Runa y Vivar no pelean por el header. El header es el dispositivo.

---

## 6. Tratamiento de estados

```
┌──────────────────────────────────────────┐
│ CRÍTICO                              1d  │  ← kicker + número display
│ Leche Tregar UAT 1L                      │  ← sans, bone
│ 24 un  ·  lote 014  ·  vence 14.08       │  ← mono, bone-dim
│ [ RETIRAR ]           [ PROMOCIÓN ]      │  ← acciones, no iconos solos
└──────────────────────────────────────────┘
     ▲
     ranura de 3px del color del nivel, pegada a la izquierda
```

| Estado | Ranura | Palabra | Acción por defecto |
|---|---|---|---|
| Vencido | #8A3530 | VENCIDO | Retirar |
| Crítico | #E07A72 | CRÍTICO | Retirar o promoción |
| Advertencia | #D4B06A | ADVERTENCIA | Promoción |
| Preventivo | #8FA37A | PREVENTIVO | Vigilar |
| Estable | #6E7A72 | ESTABLE | Ninguna (no molestar) |
| Promoción | #B7A48A | EN PROMOCIÓN | Sigue en control |
| Retirado | #5C5852 | RETIRADO | Historial |
| Agotado | #5C5852 | AGOTADO | Historial |

Copy de sistema (no corporativo, no infantil):

- “3 lotes en ventana crítica.” no “¡Atención! Tenés productos por vencer 🚨”
- “Apuntá a la carátula.” no “Subí tu archivo para comenzar”
- “Lectura hecha. Revisá y asigná vencimiento.” no “¡OCR exitoso!”
- “Ingreso activado.” no “Tus productos fueron guardados correctamente”
- “Sin lotes en esta ventana.” no “No hay datos para mostrar”

---

## 7. Iconografía

Set mínimo, trazo 1.2, viewBox 24, currentColor. Nada de filled rounded icons.

- **Ranura** — isotipo
- **Capturar** — rectángulo + punto (obturador)
- **Control** — cuatro ticks de esquina
- **Historial** — tallo + tres hairlines
- **Retirar** — ranura tapada por un cruce fino
- **Promoción** — rombo hueco
- **Protocolo** — tres sliders horizontales
- **Operador** — hexágono chico

Si un icono necesita label para entenderse, el icono sobra. En depósito, la palabra gana.

---

## 8. Pantallas clave

### 8.1 Login — VENTANA://ACCESO

```
VOID, full viewport
grain + grilla

            02  //  PROTOCOLO DE ACCESO

                  ⌬
             ventana.ia
        SYS.VENTANA  ·  SÚPER VIVAR

         [  usuario                    ]
         [  clave                      ]

              (  INGRESAR  )          ← glass, pill, tracking

         hecho por RUNA
```

### 8.2 Control — VENTANA://CONTROL

```
header: ⌬ ventana.ia          deposito
kicker: 02  //  CONTROL DE VIDA ÚTIL

┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│  3  │ │  5  │ │  8  │ │ 21  │     números en Serif
│CRÍT │ │ADV  │ │PREV │ │EST  │
└─────┘ └─────┘ └─────┘ └─────┘

filtros: TODOS  CRÍTICO  ADVERTENCIA  PROMOCIÓN

lista de lotes (ver §6)

dock mobile:
  CONTROL     ( ⌬ CAPTURAR )     HISTORIAL
                   ↑
              botón primario, ranura
```

### 8.3 Captura — VENTANA://CAPTURA

```
01  //  CAPTURA DE INGRESO

Apuntá a la carátula.

┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│                         │
│     [  obturador  ]     │     frame con ticks
│                         │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘

     (  ACTIVAR LECTURA  )

     o cargar sin foto →
```

Al leer: la foto se queda, una scan line recorre el frame, kicker cambia a `LEYENDO DOCUMENTO`.

### 8.4 Revisión — VENTANA://INGRESO

```
03  //  UN VENCIMIENTO POR PRODUCTO
C-1647 · FC 14-712036          0 / 29
Ingreso LOGICOM · 13.08
Cada producto tiene su ventana.

┌ 01 ──────────────────────────┐
│ ALFAJOR GOAT BONOBON X75GR   │
│  −  42  un  +                │
│  +7 +15 +30 +60 +90 +180     │
│  +365   NO VENCE             │
│  [ fecha de ESTA línea ]     │
└──────────────────────────────┘
┌ 02 ──────────────────────────┐
│ MOGUL EXTREME SANDIA X80GR   │
│  … su propia fecha           │
└──────────────────────────────┘

     (  CONFIRMAR 29 LOTES  )
```

### 8.5 Lote

```
04  //  LOTE 014
número 1  (serif, enorme)
CRÍTICO  ·  1 DÍA  ·  vence 14.08

Leche Tregar UAT 1L
24 un  ·  ingreso 13.08

[ RETIRAR DE CIRCULACIÓN ]
[ ACTIVAR PROMOCIÓN ]
cantidad  −  24  +
notas
```

---

## 9. Microinteracciones

| Evento | Gesto |
|---|---|
| Lectura de remito | Scan line 18s-feel, una sola pasada de 1.8s, color rune 8% |
| Confirmar ingreso | Flash de borde rune 240ms + copy “Ingreso activado.” |
| Crítico en lista | Pulso de ranura 2.8s ease, opacity 0.55↔1 |
| Tap en CTA | scale 0.985, 180ms |
| Cambio de filtro | sin bounce; el número de la tira se queda, la lista se recorta |
| Reduced motion | todo apagado. El sistema sigue siendo legible en estático |

---

## 10. Por qué no Streamlit

Streamlit impone chrome, sidebar, bloques y una densidad de desktop. El depósito entra con el pulgar, con una foto, en siete segundos. Runa exige control de cada hairline.

**ventana.ia se construye en FastAPI + HTML/CSS propio.** Python se queda donde aporta (visión, SQLite, Telegram). La superficie es del dispositivo, no del framework.

Eso no es capricho de arte: es la condición para que la activación se sienta colocada, no instalada.
