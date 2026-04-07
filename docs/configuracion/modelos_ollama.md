# Modelos Ollama Recomendados

Guia de modelos Ollama recomendados para IGV segun el hardware disponible.

## Requisitos de Memoria

De 8 GB de RAM disponibles, aproximadamente 4-5 GB son utilisables para el modelo de IA. El resto lo ocupa el sistema operativo y otras aplicaciones.

| Configuracion | Modelo maximo recomendado | Cuantizacion |
| :--- | :--- | :--- |
| 8 GB RAM | 3-7B parametros | Q4_K_M |
| 16 GB RAM | 7-14B parametros | Q4_K_M |
| 32+ GB RAM | 14B+ parametros | Q8 |

## Modelos Recomendados por Tarea

### Para Codigo (Code Generation)

| Modelo | RAM | Velocidad CPU | Recomendado para |
| :--- | :--- | :--- | :--- |
| Qwen 2.5 Coder 3B | ~2.2 GB | ~8 tok/s | Autocompletado, generacion de funciones |
| DeepSeek Coder 1.3B | ~1 GB | ~10 tok/s | Autocompletado ligero en IDE |
| Phi-4 Mini | ~2.3 GB | ~8 tok/s | Balance code + text |

### Para Texto y Chat

| Modelo | RAM | Velocidad CPU | Recomendado para |
| :--- | :--- | :--- | :--- |
| Llama 3.2 3B | ~2 GB | ~9 tok/s | Chat general, summarizacion |
| Gemma 2B | ~1.6 GB | ~10 tok/s | Respuestas rapidas, minima carga |
| Phi-3 Mini | ~2.3 GB | ~8 tok/s | Uso diario, balance calidad |

### Para Razonamiento

| Modelo | RAM | Velocidad CPU | Recomendado para |
| :--- | :--- | :--- | :--- |
| DeepSeek R1 8B | ~5 GB | ~3 tok/s | Matematicas, debugging, logica |
| Qwen 3 8B | ~5 GB | ~3 tok/s | Multilingue, matematicas |

## Configuracion para CPU-Only

Para mejorar el rendimiento en sistemas sin GPU dedicada:

```bash
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_CTX_SIZE=4096
```

En Windows, configurar via PowerShell:

```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_MAX_LOADED_MODELS", "1", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "1", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_CTX_SIZE", "4096", "User")
```

## Modelos Recomendados para IGV

Para el caso de uso de IGV (generar mensajes de tags con IA):

| Modelo | Por que |
| :--- | :--- |
| **Phi-4 Mini** | Mejor balance calidad-rendimiento para CPU |
| **Qwen 2.5 Coder 3B** | Especializado en codigo, buen rendimiento |
| **Llama 3.2 3B** | Muy popular, buena calidad general |
| **llama3.2:latest** | Modelo oficial llama, disponible por defecto |

## Instalacion de Modelos

```bash
# Instalar modelo recomendado
ollama pull phi4-mini

# Ver modelos instalados
ollama list

# Ver modelo en uso actual
ollama ps
```

## Solucion de Problemas

### El modelo no inicia

Causa: Modelo muy grande para la RAM disponible.

Solucion: Usar modelos 3B en lugar de 7B, o cerrar todas las aplicaciones.

### Respuestas lentas

Causa: Contexto muy grande o modelo en disco (swap).

Solucion: Reducir OLLAMA_CTX_SIZE a 2048 o 4096.

### Error 404 page not found

Causa: El modelo no esta descargado o nombre incorrecto.

Solucion: Verificar con `ollama list` que el modelo existe.

### Error de conexion

Causa: Ollama no esta corriendo.

Solucion: Ejecutar `ollama serve` en otra terminal.

## Recursos

- [Ollama Model Library](https://ollama.com/library)
- [Best Ollama Models for 8GB RAM](https://webscraft.org/blog/ollama-na-8-gb-ram-yaki-modeli-pratsyuyut-u-2026?lang=en)
