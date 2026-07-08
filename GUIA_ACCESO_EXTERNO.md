# Acceso exterior seguro con Caddy

Esta guia explica como publicar CuadernoPro hacia Internet usando Caddy como
proxy inverso dentro de Docker Compose.

El uso local normal no necesita esta configuracion. Para uso local o en una red
privada basta con arrancar CuadernoPro con:

```bash
docker compose up -d
```

## Idea general

No se recomienda abrir directamente el puerto de Streamlit a Internet. Para
acceso exterior, la opcion incluida usa Caddy como entrada publica:

- Caddy recibe el trafico HTTP/HTTPS.
- Caddy solicita y renueva certificados HTTPS para un dominio valido.
- Caddy aplica autenticacion basica.
- Caddy reenvia el trafico internamente a `cuadernopro:8501`.

Esta configuracion no promete seguridad absoluta. Es una capa practica de
proteccion que debe acompanarse de contrasenas fuertes, backups y mantenimiento.

## Requisitos

- Un dominio o subdominio, por ejemplo `cuadernopro.ejemplo.es`.
- DNS del dominio apuntando a la IP publica del servidor.
- Puertos 80 y 443 del router redirigidos al equipo donde corre CuadernoPro.
- Docker y Docker Compose instalados.
- No estar bajo CG-NAT. Si hay CG-NAT, conviene usar VPN o un tunel gestionado
  por un tecnico.

## Activacion

1. Crea o revisa el archivo `.env`:

```bash
cp .env.example .env
```

2. Edita `.env` y configura el dominio:

```dotenv
CUADERNOPRO_DOMAIN=cuadernopro.ejemplo.es
CUADERNOPRO_BIND_ADDRESS=127.0.0.1
```

`CUADERNOPRO_BIND_ADDRESS=127.0.0.1` limita el puerto local de Streamlit al
propio servidor. Asi, la entrada exterior debe ser Caddy y no el puerto
`CUADERNOPRO_PORT`.

3. Genera el hash de la contrasena:

```bash
./proxy_hash_password.sh
```

El script pide usuario y contrasena, genera un hash con Caddy y actualiza `.env`
si existe. No guarda ni muestra la contrasena en claro.

4. Arranca CuadernoPro con el proxy:

```bash
./start_proxy.sh
```

Tambien puede arrancarse manualmente con:

```bash
docker compose --profile proxy up -d --build
```

## Acceso

Una vez configurado el DNS y arrancado el proxy:

```text
https://cuadernopro.ejemplo.es
```

El navegador pedira el usuario y la contrasena configurados.

## Puertos

El perfil `proxy` publica Caddy en los puertos 80 y 443. CuadernoPro sigue
escuchando internamente en `cuadernopro:8501`. El script `start_proxy.sh`
comprueba que `CUADERNOPRO_BIND_ADDRESS` este limitado a `127.0.0.1` para que
Streamlit no quede publicado directamente en interfaces externas.

No abras directamente a Internet el puerto de Streamlit, como 8501 o 8503. Si
mantienes `CUADERNOPRO_PORT` para acceso local, limita su exposicion con firewall
o reglas del router.

## Seguridad

- Usa una contrasena fuerte y unica.
- No publiques directamente el puerto 8501/8503 en Internet.
- Haz backup antes de activar acceso exterior.
- Revisa periodicamente los logs:

```bash
docker compose --profile proxy logs -f caddy
docker compose --profile proxy logs -f cuadernopro
```

- Actualiza CuadernoPro, Docker y las imagenes de contenedor periodicamente.
- Revisa quien conoce el dominio y las credenciales.

## Alternativas

- Usar CuadernoPro solo en local.
- Acceder mediante VPN.
- Usar un tunel gestionado por un tecnico.

Estas alternativas pueden ser preferibles si no se controla el router, si hay
CG-NAT o si se necesita una politica de seguridad mas estricta.
