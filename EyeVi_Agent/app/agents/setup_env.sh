#!/bin/bash

# EyeVi Agent System - Deployment Script
# Script để setup và deploy hệ thống EyeVi Agent

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 EyeVi Agent System - Deployment Manager${NC}"
echo "=============================================="

# Check if we're in the right directory
if [ ! -d "host_agent" ] || [ ! -d "order_agent" ] || [ ! -d "advisor_agent" ] || [ ! -d "search_agent" ]; then
    echo -e "${RED}❌ Vui lòng chạy script này trong thư mục app/agents/${NC}"
    echo "Cấu trúc thư mục cần có: host_agent/, order_agent/, advisor_agent/, search_agent/"
    exit 1
fi

# Function to copy .env files
copy_env_files() {
    echo -e "${BLUE}📁 Copying configured .env files to agent folders...${NC}"
    
    # Check if .env.example files exist
    missing_files=false
    env_files=("host_agent.env.example" "order_agent.env.example" "advisor_agent.env.example" "search_agent.env.example")
    
    for file in "${env_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}❌ Missing $file${NC}"
            missing_files=true
        fi
    done
    
    if [ "$missing_files" = true ]; then
        echo -e "${RED}Một số file .env.example bị thiếu!${NC}"
        exit 1
    fi
    
    # Copy configured .env.example files to each agent folder
    cp host_agent.env.example host_agent/.env
    echo -e "${GREEN}✅ host_agent/.env${NC}"
    
    cp order_agent.env.example order_agent/.env
    echo -e "${GREEN}✅ order_agent/.env${NC}"
    
    cp advisor_agent.env.example advisor_agent/.env
    echo -e "${GREEN}✅ advisor_agent/.env${NC}"
    
    cp search_agent.env.example search_agent/.env
    echo -e "${GREEN}✅ search_agent/.env${NC}"
    
    echo
    echo -e "${GREEN}🎉 Copy hoàn tất! Các file .env đã được deploy vào từng agent folder.${NC}"
}

# Function to deploy system
deploy_system() {
    echo -e "${BLUE}🐳 Starting EyeVi Agent System with Docker Compose...${NC}"
    
    # Check if .env files exist
    missing_env=false
    agents=("host_agent" "order_agent" "advisor_agent" "search_agent")
    
    for agent in "${agents[@]}"; do
        if [ ! -f "${agent}/.env" ]; then
            echo -e "${RED}❌ Missing ${agent}/.env${NC}"
            missing_env=true
        fi
    done
    
    if [ "$missing_env" = true ]; then
        echo -e "${RED}Một số file .env bị thiếu. Vui lòng chạy option 1 trước.${NC}"
        exit 1
    fi
    
    # Start docker-compose
    echo -e "${BLUE}Building and starting containers...${NC}"
    docker-compose up -d
    
    echo
    echo -e "${GREEN}🎉 Deployment hoàn tất!${NC}"
    echo
    echo -e "${BLUE}📊 Kiểm tra trạng thái:${NC}"
    docker-compose ps
    
    echo
    echo -e "${BLUE}🔗 Service URLs:${NC}"
    echo "  • Host Agent:    http://localhost:8080"
    echo "  • Order Agent:   http://localhost:10000"
    echo "  • Advisor Agent: http://localhost:10001"
    echo "  • Search Agent:  http://localhost:10002"
    
    echo
    echo -e "${BLUE}📋 Useful commands:${NC}"
    echo "  • View logs:     docker-compose logs -f"
    echo "  • Stop system:   docker-compose down"
    echo "  • Restart:       docker-compose restart"
}

# Function to deploy system with no cache
deploy_system_no_cache() {
    echo -e "${BLUE}🔨 Building and deploying with no cache (fresh build)...${NC}"
    
    # Check if .env files exist
    missing_env=false
    agents=("host_agent" "order_agent" "advisor_agent" "search_agent")
    
    for agent in "${agents[@]}"; do
        if [ ! -f "${agent}/.env" ]; then
            echo -e "${RED}❌ Missing ${agent}/.env${NC}"
            missing_env=true
        fi
    done
    
    if [ "$missing_env" = true ]; then
        echo -e "${RED}Một số file .env bị thiếu. Vui lòng chạy option 1 trước.${NC}"
        exit 1
    fi
    
    # Stop any running containers first
    echo -e "${BLUE}Stopping existing containers...${NC}"
    docker-compose down
    
    # Build with no cache and start
    echo -e "${BLUE}Building containers with no cache...${NC}"
    docker-compose build --no-cache
    
    echo -e "${BLUE}Starting fresh containers...${NC}"
    docker-compose up -d
    
    echo
    echo -e "${GREEN}🎉 Fresh deployment hoàn tất!${NC}"
    echo
    echo -e "${BLUE}📊 Kiểm tra trạng thái:${NC}"
    docker-compose ps
    
    echo
    echo -e "${BLUE}🔗 Service URLs:${NC}"
    echo "  • Host Agent:    http://localhost:8080"
    echo "  • Order Agent:   http://localhost:10000"
    echo "  • Advisor Agent: http://localhost:10001"
    echo "  • Search Agent:  http://localhost:10002"
}

# Function to show menu
show_menu() {
    echo
    echo -e "${BLUE}📋 Chọn hành động:${NC}"
    echo "  1) Copy .env files và deploy system"
    echo "  2) Deploy system (chỉ chạy docker-compose)"
    echo "  3) Build và deploy no cache (fresh build)"
    echo "  4) Stop system (docker-compose down)"
    echo "  5) View logs"
    echo "  6) Exit"
    echo
    echo -e "${YELLOW}💡 Lưu ý: Trước khi chọn option 1, hãy chỉnh sửa các file:${NC}"
    echo "     host_agent.env.example, order_agent.env.example,"
    echo "     advisor_agent.env.example, search_agent.env.example"
    echo
}

# Function to stop system
stop_system() {
    echo -e "${BLUE}🛑 Stopping EyeVi Agent System...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ System stopped${NC}"
}

# Function to view logs
view_logs() {
    echo -e "${BLUE}📋 Chọn logs để xem:${NC}"
    echo "  1) All services"
    echo "  2) Host Agent"
    echo "  3) Order Agent"
    echo "  4) Advisor Agent"
    echo "  5) Search Agent"
    echo "  6) Back to main menu"
    echo
    read -p "Nhập lựa chọn (1-6): " log_choice
    
    case $log_choice in
        1)
            echo -e "${BLUE}📄 Showing logs for all services (Ctrl+C to exit)...${NC}"
            docker-compose logs -f
            ;;
        2)
            echo -e "${BLUE}📄 Showing Host Agent logs (Ctrl+C to exit)...${NC}"
            docker-compose logs -f host_agent
            ;;
        3)
            echo -e "${BLUE}📄 Showing Order Agent logs (Ctrl+C to exit)...${NC}"
            docker-compose logs -f order_agent
            ;;
        4)
            echo -e "${BLUE}📄 Showing Advisor Agent logs (Ctrl+C to exit)...${NC}"
            docker-compose logs -f advisor_agent
            ;;
        5)
            echo -e "${BLUE}📄 Showing Search Agent logs (Ctrl+C to exit)...${NC}"
            docker-compose logs -f search_agent
            ;;
        6)
            return
            ;;
        *)
            echo -e "${RED}❌ Invalid choice${NC}"
            ;;
    esac
}

# Main menu loop
while true; do
    show_menu
    read -p "Nhập lựa chọn (1-6): " choice
    
    case $choice in
        1)
            echo -e "${YELLOW}⚠️  Đảm bảo bạn đã chỉnh sửa các file *.env.example với config thực tế!${NC}"
            read -p "Bạn đã chỉnh sửa các file *.env.example chưa? (y/N): " env_ready
            if [[ $env_ready == "y" || $env_ready == "Y" ]]; then
                copy_env_files
                deploy_system
            else
                echo -e "${YELLOW}⚠️  Vui lòng chỉnh sửa các file *.env.example trước:${NC}"
                echo "  • host_agent.env.example"
                echo "  • order_agent.env.example"
                echo "  • advisor_agent.env.example"
                echo "  • search_agent.env.example"
            fi
            ;;
        2)
            deploy_system
            ;;
        3)
            deploy_system_no_cache
            ;;
        4)
            stop_system
            ;;
        5)
            view_logs
            ;;
        6)
            echo -e "${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid choice. Please enter 1-6${NC}"
            ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
done 