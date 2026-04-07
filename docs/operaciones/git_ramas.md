# Ramas Git

Estrategia de branching para desarrollo, releases y hotfixes.

## Modelo de Ramas

| Rama | Propósito | Origen | Destino |
| :--- | :--- | :--- | :--- |
| `main` | Producción | - | - |
| `develop` | Desarrollo activo | main | release/*, main |
| `feature/*` | Nuevas funcionalidades | develop | develop |
| `release/*` | Preparación versión | develop | main, develop |
| `hotfix/*` | Correcciones críticas | main | main, develop |

## Flujo de Trabajo

### Feature (Nueva funcionalidad)

```bash
# 1. Crear rama desde develop
git checkout -b feature/nombre-feature develop

# 2. Trabajar y hacer commits
git add .
git commit -m "feat: descripción"

# 3. Mergear a develop
git checkout develop
git merge feature/nombre-feature

# 4. Eliminar rama
git branch -d feature/nombre-feature
```

### Release (Preparación de versión)

```bash
# 1. Crear rama desde develop
git checkout -b release/v1.2.0 develop

# 2. Cambiar versión en pyproject.toml
# 3. Hacer commits de ajustes finales
git add .
git commit -m "chore: versión preparada para release"

# 4. Mergear a main
git checkout main
git merge release/v1.2.0

# 5. Crear tag
git tag v1.2.0

# 6. Mergear cambios a develop
git checkout develop
git merge release/v1.2.0

# 7. Eliminar rama
git branch -d release/v1.2.0
```

### Hotfix (Corrección urgente)

```bash
# 1. Crear rama desde main
git checkout -b hotfix/v1.2.1 main

# 2. Corregir el bug
git add .
git commit -m "fix: corrección crítica"

# 3. Mergear a main
git checkout main
git merge hotfix/v1.2.1

# 4. Crear tag
git tag v1.2.1

# 5. Mergear a develop
git checkout develop
git merge hotfix/v1.2.1

# 6. Eliminar rama
git branch -d hotfix/v1.2.1
```

## Comandos Útiles

| Comando | Descripción |
| :--- | :--- |
| `git branch -a` | Listar todas las ramas |
| `git branch -d rama` | Eliminar rama local (seguro) |
| `git branch -D rama` | Eliminar rama local (forzado) |
| `git push origin --delete rama` | Eliminar rama remota |
| `git checkout -b rama origen` | Crear y cambiar a nueva rama |
| `git merge rama` | Mergear rama actual |

## Reglas

1. No hacer commit directamente en `main`
2. Eliminar ramas después de merge
3. Tags solo en `main` para releases
4. Hotfixes requieren versión bump

| Campo | Valor |
| :--- | :--- |
| **Mantenedor** | amillanaol(https://orcid.org/0009-0003-1768-7048) |
| **Estado** | Final |
| **Última Actualización** | 2026-02-14 |
