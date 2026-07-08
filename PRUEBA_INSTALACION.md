# Prueba de Instalacion desde ZIP

Guia para probar CuadernoPro desde un ZIP limpio generado con `git archive`.
La prueba debe hacerse en una carpeta temporal y con un puerto distinto si ya
existe otra instalacion en el mismo servidor.

## 1. Crear carpeta temporal

```bash
cd ~
mkdir -p prueba_instalacion_cuadernopro
cd prueba_instalacion_cuadernopro
```

## 2. Copiar ZIP

```bash
cp ~/cuadernopro/backups/cuadernopro_codigo_v4_4_release_interna.zip .
```

## 3. Descomprimir

```bash
unzip cuadernopro_codigo_v4_4_release_interna.zip
cd cuadernopro-v4.4-release-interna
```

## 4. Crear `.env`

```bash
cat > .env <<'EOF'
COMPOSE_PROJECT_NAME=cuadernopro_prueba
CUADERNOPRO_PORT=8504
TZ=Europe/Madrid
CUADERNOPRO_DB_PATH=/app/runtime/cuadernopro.db
CUADERNOPRO_BACKUPS_DIR=/app/runtime/backups
CUADERNOPRO_EXPORTS_DIR=/app/runtime/exports
CUADERNOPRO_DOCUMENTOS_DIR=/app/runtime/documentos
EOF
```

Crear las carpetas persistentes:

```bash
mkdir -p runtime/backups runtime/exports runtime/documentos
```

## 5. Arrancar

```bash
docker compose up -d --build
```

## 6. Comprobar

```bash
docker compose ps
docker compose logs --tail=80 cuadernopro
```

El contenedor debe quedar publicado en el puerto configurado, por ejemplo
`8504`, y no debe existir conflicto con otras instalaciones.

## 7. Entrar

Abrir en el navegador:

```text
http://IP_DEL_SERVIDOR:8504
```

En una prueba local tambien puede usarse:

```text
http://localhost:8504
```

## 8. Prueba funcional minima

- Crear campaña.
- Rellenar datos de explotacion.
- Crear backup.
- Resetear base.
- Restaurar backup.
- Comprobar que los datos restaurados son visibles.

## 9. Apagar

```bash
docker compose down
```

## 10. Borrar carpeta temporal

Si la prueba ha terminado y no se necesitan los datos generados:

```bash
cd ~
rm -rf ~/prueba_instalacion_cuadernopro
```
