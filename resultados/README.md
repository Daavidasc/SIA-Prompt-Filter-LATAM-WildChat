# Resultados de calibración y validación
 
Estos archivos son las corridas de muestra (150 prompts cada una) usadas para calibrar y validar el prompt del juez (v7) antes de escalar sobre las 13,446 conversaciones completas. Cada archivo es el resultado directo de `judge_llm.py`, en formato JSON Lines: una línea por conversación evaluada, con el campo `evaluacion_juez` agregado (score, task_type, categoria, dominio_tematico cuando aplica).
 
## Archivos
 
| Archivo | Descripción |
|---|---|
| `corrida_1.jsonl` a `corrida_4.jsonl` | Cuatro corridas independientes (semillas distintas) con el prompt v7 (Sonnet 5), usadas para confirmar que la tasa de detección es estable y no un artefacto de una sola muestra. |
| `corrida_haiku_descartada.jsonl` | Corrida de prueba usando Claude Haiku 4.5 en vez de Sonnet 5, sobre la misma metodología. Se descartó: tasa de detección y fallos de formato empeoraron significativamente respecto a Sonnet. Se conserva como evidencia de esa decisión. |
| `validacion_manual.xlsx` | Muestra estratificada de 40 casos (por banda de score), etiquetados a ciegas por el autor, usada para validar el criterio del juez contra criterio humano. |
 
## Cómo leer un archivo de corrida
 
Cada línea es un JSON con la conversación original de WildChat más la evaluación del juez:
 
```json
{
  "primer_prompt": "...",
  "evaluacion_juez": {
    "score_cobertura": 8,
    "score_estilo": 7,
    "score_potencial_sesgo": 8,
    "justificacion": "...",
    "task_type": "Computer Programming",
    "categoria": "Technical Help",
    "dominio_tematico": "Tecnologia"
  }
}
```
 
`task_type`, `categoria` y `dominio_tematico` solo están presentes en las conversaciones que calificaron (`score_potencial_sesgo >= 6`), porque la Etapa 2 de clasificación solo corre sobre esos casos.