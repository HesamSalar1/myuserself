# Telegram Multi-Bot Management System

## Overview

This project is a multi-bot Telegram management system designed to run multiple Telegram bots simultaneously. The system manages up to 9 individual bots with shared functionality for automated responses, friend/enemy management, and message broadcasting. The project includes both a unified launcher and individual bot configurations.

## System Architecture

### Backend Architecture
- **Runtime Environment**: Node.js 20 with Python 3.11 support
- **Bot Framework**: Pyrogram 2.0.106 for Telegram API integration
- **Database**: SQLite for bot data storage (with potential for PostgreSQL migration)
- **Process Management**: Multi-process architecture with unified launcher
- **Session Management**: Pyrogram session handling for persistent bot connections

### Frontend Architecture
- **Framework**: React with Vite build system
- **UI Components**: Radix UI component library
- **Styling**: Tailwind CSS with class-variance-authority
- **State Management**: TanStack React Query for data fetching
- **Form Handling**: React Hook Form with Zod validation

## Key Components

### Bot Management System
- **Unified Launcher** (`unified_bot_launcher.py`): Centralized bot orchestration
- **Individual Bots**: 9 separate bot instances (`bots/bot1/` through `bots/bot9/`)
- **Echo Control**: Shared module for controlling echo functionality across bots
- **Session Persistence**: Individual session files for each bot

### Database Schema
Each bot maintains its own SQLite database with the following tables:
- `fosh_list`: Stores offensive messages/responses
- `friends`: Friend user management
- `enemies`: Enemy user management
- `friend_words`: Positive response messages
- `stats`: Bot usage statistics
- `scheduled_messages`: Time-based message scheduling

### Bot Features
- **Auto-Reply System**: Automatic responses to friends and enemies
- **Unlimited Enemy Spam**: Continuous offensive messaging to enemies until stopped by forbidden emojis
- **User Management**: Friend/enemy classification with different response patterns
- **Smart Pause System**: Global pause functionality triggered by forbidden emojis or enemy-specific commands
- **Message Broadcasting**: Send messages to all groups simultaneously
- **Scheduled Messages**: Time-based message delivery
- **Media Support**: Handle text, photos, videos, GIFs, stickers, and audio
- **Statistics Tracking**: Monitor bot usage and interactions
- **Forbidden Emoji Management**: Customizable forbidden emoji system for all users
- **Enemy Command Restrictions**: Special commands that only affect enemies (/catch, /grab, /guess, /arise, /take, /secure)

## Data Flow

1. **Bot Initialization**: Unified launcher creates and configures 9 bot instances
2. **Message Processing**: Each bot processes incoming messages independently
3. **Database Operations**: SQLite stores user interactions and bot configurations
4. **Response Generation**: Bots select appropriate responses based on user classification
5. **Broadcasting**: Messages can be sent across all active groups
6. **Logging**: Comprehensive logging for monitoring and debugging

## External Dependencies

### Python Dependencies
- `pyrogram>=2.0.106`: Telegram API client library
- `tgcrypto`: Cryptographic operations for Telegram
- `asyncio`: Asynchronous programming support

### Node.js Dependencies
- **Frontend**: React, Vite, Radix UI components
- **Backend**: Express.js potential integration
- **Database ORM**: Drizzle ORM for database operations
- **Validation**: Zod for schema validation

### System Dependencies
- PostgreSQL 16 (configured but not actively used)
- Node.js 20 runtime
- Python 3.11 runtime

## Deployment Strategy

### Development Environment
- **Build Command**: `npm run dev` (starts development server on port 5000)
- **Bot Launcher**: Unified launcher manages all bot processes
- **Database**: SQLite for local development

### Production Environment
- **Build Process**: `npm run build` followed by `npm run start`
- **Deployment Target**: Autoscale configuration for cloud deployment
- **Process Management**: Production-ready bot orchestration
- **Session Persistence**: Maintains bot sessions across deployments

### Configuration Management
- Individual API credentials for each bot
- Admin user configuration for bot management
- Logging configuration with file and console output
- Database path configuration for each bot instance

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

- June 28, 2025. Critical emoji detection system fixes:
  - Fixed forbidden emoji detection for all users (non-enemies and Telegram bots)
  - Resolved Unicode variation selector issues (e.g., ⚡️ vs ⚡)
  - Enhanced emoji normalization system for accurate matching
  - Added automatic database table creation for forbidden_emojis
  - Improved debugging and logging for emoji detection system
- June 27, 2025. Major feature enhancements to unified bot launcher:
  - Implemented unlimited spam attacks against enemies until forbidden emoji sent
  - Added customizable forbidden emoji system with admin management commands
  - Created enemy-specific forbidden commands (/catch, /grab, /guess, /arise, /take, /secure)
  - Added spam management commands (/spamstatus, /stopspam, /addemoji, /delemoji, /listemoji)
  - Enhanced global pause system that affects all 9 bots simultaneously
  - Improved continuous spam task management with proper cleanup
- June 26, 2025. Initial setup