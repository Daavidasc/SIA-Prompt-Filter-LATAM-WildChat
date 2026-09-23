# SIA-Prompt-Filter-LATAM-WildChat
Filtra, de un corpus real de conversaciones con LLMs en español latinoamericano (WildChat-1M), los prompts con mayor potencial de mostrar sesgo en cómo un modelo trata al usuario que le habla (no en cómo describe a terceros). El resultado es un conjunto de prompts "limpios" — neutros, sin identidad revelada, con margen real de trato distinto según el perfil del usuario — listos para usarse en un experimento posterior de inyección de perfiles.

## Estructura

```
filtro_inicial.py            → filtra WildChat-1M por idioma (español) y país (LATAM)
judge_llm.py                 → evalúa cada prompt en dos etapas: puntúa potencial de sesgo y clasifica los que califican
preparar_candidatos.py       → extrae los candidatos filtrados a un Excel organizado por dominio, con resumen y gráficos
```
 ## Setup
 
```bash
pip install anthropic python-dotenv openpyxl
```
 
Crear un archivo `.env` en la raíz del proyecto:
 
```
ANTHROPIC_API_KEY=sk-ant-...
HF_TOKEN=hf_...
```
 
(Se necesita una cuenta de Hugging Face con la licencia de WildChat-1M aceptada para el Paso 1.)
 
## Uso
 
```bash
python 01_filtrar_wildchat.py
python judge_llm.py
python preparar_candidatos.py
```
 
1. `01_filtrar_wildchat.py` genera `wildchat_latam_es_completo.jsonl` con las conversaciones filtradas.
2. `judge_llm.py` lee ese archivo, evalúa cada prompt, y guarda el resultado en `muestra_evaluada.jsonl`. Los parámetros `TAMANO_MUESTRA` y `SEMILLA_ALEATORIA` controlan si corre sobre una muestra o sobre el archivo completo.
3. `preparar_candidatos.py` lee `muestra_evaluada.jsonl` y genera `candidatos.xlsx`, listo para revisión manual.
