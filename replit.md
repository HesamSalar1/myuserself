# Telegram Multi-Bot Management System

## Overview

This project is a multi-bot Telegram management system designed to run multiple Telegram bots simultaneously. The system manages up to 9 individual bots with shared functionality for automated responses, friend/enemy management, and message broadcasting. It includes a unified launcher for orchestration and individual bot configurations for tailored operations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Runtime Environment**: Node.js 20 with Python 3.11 support
- **Bot Framework**: Pyrogram 2.0.106 for Telegram API integration
- **Database**: SQLite for bot data storage (with potential for PostgreSQL migration)
- **Process Management**: Multi-process architecture with a unified launcher orchestrating 9 separate bot instances.
- **Session Management**: Pyrogram session handling for persistent bot connections.
- **Bot Features**:
    - Auto-Reply System: Automatic responses to friends and enemies.
    - Unlimited Enemy Spam: Continuous offensive messaging to enemies until stopped by forbidden emojis.
    - User Management: Friend/enemy classification with different response patterns.
    - Smart Pause System: Global and per-chat pause functionality triggered by forbidden emojis or enemy-specific commands.
    - Message Broadcasting: Send messages to all groups simultaneously.
    - Scheduled Messages: Time-based message delivery.
    - Media Support: Handle text, photos, videos, GIFs, stickers, and audio.
    - Statistics Tracking: Monitor bot usage and interactions.
    - Enhanced Forbidden Content Management: Zero-default system with full Telegram-based configuration for both emojis and words.
    - Advanced Unicode Detection: Bulletproof emoji detection with variation selector and normalization support.
    - Intelligent Word Matching: Per-word case sensitivity and partial/exact matching with regex support.
    - Comprehensive Security Check: Multi-layer detection engine with emoji + word validation and security logging.
    - Performance-Optimized Detection: Sub-millisecond detection with intelligent caching and batch processing.
    - Emergency Isolation System: Per-chat security stops with comprehensive reporting and automatic recovery.
    - Real-time Security Monitoring: Live statistics, audit trails, and detailed security logs.
    - Database-Backed Configuration: Persistent storage with advanced management functions.
    - Enemy Command Restrictions: Special commands that only affect enemies (/catch, /grab, /guess, /arise, /take, /secure).
    - Natural Auto-Conversation System: Each bot has a unique personality with diverse, context-aware messages in mixed languages (Persian/English/Hindi).
    - Per-Chat Isolation System: Emergency stop, rate limiting, and spam management operate independently per chat.
    - Global Rate Limiting: Shared locks across all bots per chat to prevent message flooding.
    - Configurable Spam Delay System: Customizable delay settings for enemy attack frequency.
    - Advanced Admin Permission System: Hierarchical admin control with a main launcher admin and individual bot admins.

### Frontend Architecture
- **Framework**: React with Vite build system
- **UI Components**: Radix UI component library
- **Styling**: Tailwind CSS with class-variance-authority
- **State Management**: TanStack React Query for data fetching
- **Form Handling**: React Hook Form with Zod validation
- **Web Panel Management Interface**: For monitoring bot integration.

### Deployment Architecture
- **Development Environment**: Local development with SQLite, `npm run dev` for frontend.
- **Production Environment**: Autoscale configuration, `npm run build` and `npm run start`.
- **VPS Deployment System**:
    - **Docker Configuration**: Dockerfile and `docker-compose.yml` for containerization.
    - **StackHost Integration**: `stackhost.yaml` for cloud deployment.
    - **System Management**: VPS manager, monitoring system, configuration management.
    - **Service Management**: SystemD service files for all components.
    - **Nginx Configuration**: Load balancer and reverse proxy.
    - **Database Setup**: PostgreSQL with schema and initialization.
    - **Backup System**: Automated backup with S3 integration.
    - **Security**: SSL/TLS, rate limiting, access control.
    - **Monitoring**: Advanced system monitoring with alerts.

## External Dependencies

- **Python Libraries**: `pyrogram>=2.0.106`, `tgcrypto`, `asyncio`
- **Node.js Libraries**: React, Vite, Radix UI, Drizzle ORM, Zod, Express.js (potential integration)
- **Databases**: SQLite, PostgreSQL 16
- **System Runtimes**: Node.js 20, Python 3.11
- **Monitoring Bot**: Telegram bot (Token: 7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk) for real-time reporting.
- **Enhanced Security Commands**: Complete Telegram interface for managing forbidden emojis and words without file editing.
- **Performance Testing Suite**: Comprehensive test system for validating detection accuracy and performance.