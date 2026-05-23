# ¿Quién quiere ser millonario? — Edición Bíblica

Juego tipo *Who Wants to Be a Millionaire* en Streamlit.

## Estructura del proyecto

```
biblia_game/
├── app.py                 # Entrada Streamlit (ejecutar este archivo)
├── requirements.txt
├── README.md
├── data/
│   └── preguntas.txt      # Banco de preguntas del juego
├── assets/
│   └── audio/             # Efectos de sonido (.wav)
└── src/
    ├── config.py          # Rutas del proyecto
    ├── app_main.py        # Lógica principal del juego
    ├── parser.py          # Lectura de preguntas
    ├── questions_io.py    # Guardar / exportar preguntas
    ├── question_admin.py  # Panel gestión de preguntas
    ├── audio_assets.py    # Generación de sonidos
    └── sound_player.py    # Reproducción en Streamlit
```

## Requisitos

- Python 3.10+
- Streamlit 1.37+

## Instalación y ejecución

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abrirá en el navegador (por defecto `http://localhost:8501`).

## Características

- Preguntas en **orden aleatorio** cada partida
- Escalera de premios hasta **$1,000,000** (puntos)
- Casillas seguras en las preguntas **5** y **10**
- Comodines: **50:50**, **Público** (20 s) y **Amigo** (30 s)
- Opción de **retirarse** con lo acumulado
- **Sonidos** activables desde el menú

## Gestionar preguntas

En el menú → **📝 Gestionar preguntas**:

- Ver / eliminar preguntas
- Pegar texto desde Word o WhatsApp
- Subir archivo `.txt`
- Agregar una pregunta con formulario
- Descargar plantilla o banco actual

## Formato de preguntas (`data/preguntas.txt`)

```
1. Texto de la pregunta
A. Opción A
B. Opción B
C. Opción C
D. Opción D
Respuesta correcta: B
```
