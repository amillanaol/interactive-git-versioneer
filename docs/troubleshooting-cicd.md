# Guía de Resolución de Problemas CI/CD - Interactive Git Versioneer

## ¿Qué necesito? → ¿Dónde lo busco?

| Necesidad | Ubicación |
|-----------|-----------|
| Configurar API keys en GitHub | Repository Settings → Secrets and variables → Actions |
| Ver configuración del workflow | [.github/workflows/auto-tag.yml](../.github/workflows/auto-tag.yml) |
| Validar configuración local | `python -m interactive_git_versioneer.main config set` |
| Ejecutar prueba local | `python -m interactive_git_versioneer.main tag --auto --dry-run` |

## Configuración de Secrets en GitHub

| Secreto | Valor Requerido | Propósito |
|---------|----------------|-----------|
| GROQ_API_KEY | API key de Groq | Autenticación con servicio IA |
| (opcional) OPENAI.key | API key de OpenAI | Alternativa a Groq |

### Pasos de Configuración

1. Navegar al repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. New repository secret
4. Ingresar nombre y valor del secreto
5. Confirmar creación

## Problema → Solución

| Problema | Solución |
|----------|----------|
| "Configuración de IA incompleta" | Verificar que GROQ_API_KEY exista en secrets de GitHub |
| "Error: Process completed with exit code 1" | Validar formato correcto del workflow en líneas 26-30 |
| Falla en paso "Configure API" | Confirmar variables de entorno en el contenedor CI/CD |
| No se ejecuta tagging automático | Revisar permisos: contents: write en línea 12 |

## Referencias del Código

| Funcionalidad | Archivo | Línea |
|---------------|---------|-------|
| Workflow CI/CD | `.github/workflows/auto-tag.yml` | 26-37 |
| Configuración API | Módulo main | Líneas config |
| Ejecución tagging | Módulo main | Líneas tag |

## Versión

| Versión | Generado | Estado | Comentarios |
|---------|----------|--------|-------------|
| 1.0 | 2025-02-05 | Activo | Guía inicial para problemas CI/CD con secrets de GitHub |