"""
Paso 1 del pipeline SIA: filtrar WildChat-1M por idioma español y países de
Latinoamérica, sin tener que descargar el dataset completo (streaming).

CÓMO CORRERLO:
- Este script necesita internet hacia huggingface.co, así que NO corre en el
  sandbox de Claude. Se ejecuta en tu computador o en Google Colab.
- Antes de correr: pip install datasets huggingface_hub python-dotenv
- Necesitás tu token de HF (Settings -> Access Tokens -> tipo "Read")
  El .env debe tener: HF_TOKEN=hf_...

QUÉ HACE:
1. Se conecta a WildChat-1M en modo streaming (no baja el millón de golpe)
2. Recorre las conversaciones y se queda solo con las que:
   - tienen language == "Spanish" (WildChat detecta el idioma por conversación)
   - country está en la lista de países LATAM definida abajo
3. Guarda el resultado filtrado en un .jsonl (un JSON por línea), liviano,
   listo para pasarle después al LLM-as-judge (Paso 2)
"""

from datasets import load_dataset
import json
import os
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Aviso: python-dotenv no está instalado. Instalar con: pip install python-dotenv")

# ---------------------------------------------------------------------------
# CONFIGURACIÓN — ajustar según haga falta
# ---------------------------------------------------------------------------

HF_TOKEN = os.environ.get("HF_TOKEN")  # se lee del .env, nunca hardcodear
if not HF_TOKEN:
    raise SystemExit("Falta HF_TOKEN. Agregalo al .env: HF_TOKEN=hf_...")

# Países LATAM tal como los etiqueta WildChat (nombres en inglés, formato GeoIP2)
PAISES_LATAM = {
    "Chile", "Argentina", "Mexico", "Peru", "Colombia", "Venezuela",
    "Ecuador", "Bolivia", "Paraguay", "Uruguay", "Guatemala", "Honduras",
    "El Salvador", "Nicaragua", "Costa Rica", "Panama", "Dominican Republic",
    "Cuba",
}

MAX_RESULTADOS = None  # sin tope: recorre el dataset completo (~1M conversaciones)
ARCHIVO_SALIDA = "wildchat_latam_es_completo.jsonl"

# ---------------------------------------------------------------------------
# CARGA EN STREAMING (no descarga el dataset completo a disco)
# ---------------------------------------------------------------------------

print("Conectando a WildChat-1M en modo streaming...")
ds = load_dataset(
    "allenai/WildChat-1M",
    split="train",
    streaming=True,
    token=HF_TOKEN,
)

# ---------------------------------------------------------------------------
# FILTRADO
# ---------------------------------------------------------------------------

TOTAL_APROX_DATASET = 1_009_245  # tamaño total conocido de WildChat-1M

inicio = time.time()
encontrados = 0
revisados = 0
conteo_por_pais = {}

with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f_out:
    for ejemplo in ds:
        revisados += 1

        pais = ejemplo.get("country")
        idioma = ejemplo.get("language")

        if pais in PAISES_LATAM and idioma == "Spanish":
            # Nos quedamos solo con los campos que nos interesan, para que
            # el archivo de salida sea liviano
            fila = {
                "conversation_hash": ejemplo.get("conversation_hash"),
                "country": pais,
                "state": ejemplo.get("state"),
                "language": idioma,
                "model": ejemplo.get("model"),
                "turn": ejemplo.get("turn"),
                # Solo el primer mensaje del usuario (el prompt inicial),
                # que es lo que le vamos a pasar al LLM-judge en el Paso 2
                "primer_prompt": ejemplo["conversation"][0]["content"]
                if ejemplo.get("conversation") else None,
            }
            f_out.write(json.dumps(fila, ensure_ascii=False) + "\n")

            encontrados += 1
            conteo_por_pais[pais] = conteo_por_pais.get(pais, 0) + 1

        if revisados % 50000 == 0:
            transcurrido = time.time() - inicio
            velocidad = revisados / transcurrido  # filas por segundo
            restantes = TOTAL_APROX_DATASET - revisados
            eta_seg = restantes / velocidad if velocidad > 0 else 0
            print(f"  revisados: {revisados:,} | encontrados: {encontrados:,} "
                  f"| ETA: ~{eta_seg/60:.1f} min")

        if MAX_RESULTADOS is not None and encontrados >= MAX_RESULTADOS:
            print(f"Se alcanzó el tope de {MAX_RESULTADOS}, deteniendo.")
            break

print("\n--- Resumen ---")
print(f"Total revisados: {revisados:,}")
print(f"Total encontrados (español + LATAM): {encontrados:,}")
print("Desglose por país:")
for pais, n in sorted(conteo_por_pais.items(), key=lambda x: -x[1]):
    print(f"  {pais}: {n}")
print(f"\nGuardado en: {ARCHIVO_SALIDA}")