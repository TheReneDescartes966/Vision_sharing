#!/bin/bash

# =============================================================================
# Vison - Script de Control Interactivo
# =============================================================================

set -e

COMPOSE_FILE="docker-compose.yml"
LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_docker() {
    if ! docker compose version &>/dev/null 2>&1; then
        log_error "docker compose v2 no encontrado"
        exit 1
    fi
}

setup_dirs() {
    mkdir -p recordings gst 2>/dev/null || true
    chmod 777 recordings gst 2>/dev/null || true
}

get_local_ip() {
    hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost"
}

action_start() {
    log_info "Iniciando servicios..."
    docker compose up -d --build

    log_info "Esperando a que inicien los contenedores..."
    sleep 5

    # Verificar web-ui
    local web_status
    web_status=$(docker compose ps web-ui 2>/dev/null | grep -c "Up" || echo "0")

    if [ "$web_status" -gt 0 ]; then
        log_success "Contenedor web-ui iniciado"
        echo ""
        echo "============================================"
        echo "  App disponible en:"
        echo "  http://localhost:3000"
        echo "  http://${LAN_IP}:3000"
        echo "============================================"
    else
        log_error "El contenedor web-ui no inició"
        echo ""
        log_info "Logs de web-ui:"
        docker compose logs web-ui
        exit 1
    fi

    # Verificar video-service
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        log_success "video-service: OK"
    else
        log_warning "video-service: no responde aún"
    fi
}

action_logs() {
    docker compose logs -f
}

action_stop() {
    log_info "Deteniendo servicios..."
    docker compose down
    log_success "Servicios detenidos"
}

action_restart() {
    log_info "Reiniciando servicios..."
    docker compose restart
    sleep 3

    local web_status
    web_status=$(docker compose ps web-ui 2>/dev/null | grep -c "Up" || echo "0")

    if [ "$web_status" -gt 0 ]; then
        log_success "Servicios reiniciados"
        echo ""
        echo "============================================"
        echo "  App disponible en:"
        echo "  http://localhost:3000"
        echo "  http://${LAN_IP}:3000"
        echo "============================================"
    else
        log_error "Error al reiniciar"
    fi
}

action_status() {
    log_info "Estado de servicios:"

    if docker compose ps 2>/dev/null | grep -q "vison-web-ui.*Up"; then
        log_success "web-ui: corriendo"
    else
        log_error "web-ui: detenido"
    fi

    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        log_success "video-service: OK"
    else
        log_error "video-service: no responde"
    fi

    echo ""
    echo "  http://localhost:3000"
    echo "  http://${LAN_IP}:3000"
}

show_menu() {
    echo ""
    echo "============================================"
    echo "         VISON CONTROL PANEL"
    echo "============================================"
    echo "1) Iniciar sistema"
    echo "2) Ver logs"
    echo "3) Detener sistema"
    echo "4) Reiniciar"
    echo "5) Estado"
    echo "6) Salir"
    echo "============================================"
}

main() {
    check_docker
    setup_dirs

    if [ $# -gt 0 ]; then
        case $1 in
            start) action_start ;;
            stop) action_stop ;;
            restart) action_restart ;;
            logs) action_logs ;;
            status) action_status ;;
            1) action_start ;;
            2) action_logs ;;
            3) action_stop ;;
            4) action_restart ;;
            5) action_status ;;
            6) exit 0 ;;
            *) log_error "Opción inválida" ;;
        esac
        return
    fi

    while true; do
        show_menu
        read -p "Selecciona una opción: " choice
        case $choice in
            1) action_start ;;
            2) action_logs ;;
            3) action_stop ;;
            4) action_restart ;;
            5) action_status ;;
            6)
                echo "¡Hasta luego!"
                exit 0
                ;;
            *) log_warning "Opción inválida" ;;
        esac
    done
}

main "$@"