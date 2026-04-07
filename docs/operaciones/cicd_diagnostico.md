| Necesidad | Ubicación |
| :--- | :--- |
| Configurar API keys en GitHub | Repository Settings → Secrets and variables → Actions |
| Ver workflow CI/CD | `.github/workflows/auto-tag.yml` |
| Validar configuración local | `igv config set <key> <value>` |
| Ejecutar prueba local | `igv tag --auto --dry-run` |
| Ver secrets configurados | GitHub Settings → Secrets → Actions |

## Configuración de Secrets

| Secreto | Valor | Propósito |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | API key de Groq | Autenticación IA |
| `OPENAI.key` (opcional) | API key de OpenAI | Alternativa a Groq |

Pasos: Settings → Secrets and variables → Actions → New repository secret.

## Diagnóstico de Problemas

| Síntoma | Causa Raíz | Solución Técnica |
| :--- | :--- | :--- |
| Configuración de IA incompleta | Falta `GROQ_API_KEY` en secrets | Crear secret en GitHub Settings |
| Process completed with exit code 1 | Workflow malformado | Validar YAML en líneas 26-37 de `.github/workflows/auto-tag.yml` |
| Falla en paso Configure API | Variables de entorno no inyectadas | Verificar `env:` en workflow |
| Tagging automático no ejecuta | Permisos insuficientes | Agregar `contents: write` en línea 12 del workflow |

## Referencias del Código

| Funcionalidad | Archivo | Líneas |
| :--- | :--- | :--- |
| Workflow CI/CD | `.github/workflows/auto-tag.yml` | 26-37 |
| Configuración API | `src/interactive_git_versioneer/main.py` | 175-227 |
| Ejecución tagging | `src/interactive_git_versioneer/main.py` | 228-259 |

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol([https://orcid.org/0009-0003-1768-7048](https://orcid.org/0009-0003-1768-7048)) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |
