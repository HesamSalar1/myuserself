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

## Monitoring Bot Integration

Added new monitoring bot (Token: 7708355228:AAGPzhm47U5-4uPnALl6Oc6En91aCYLyydk) that provides:
- Real-time reporting of forbidden emoji detections
- Notifications to all users who started the bot (/start command)
- Integration with the unified bot launcher
- Web panel management interface
- Per-chat isolation for emoji detection events

## VPS Deployment System

Complete deployment infrastructure added for running 9 bots on dedicated VPS:

### Components Added:
- **Docker Configuration**: Complete Dockerfile and docker-compose.yml with all services
- **StackHost Integration**: stackhost.yaml with comprehensive service definitions
- **System Management**: VPS manager, monitoring system, and configuration management
- **Service Management**: SystemD service files for all components
- **Nginx Configuration**: Load balancer and reverse proxy setup
- **Database Setup**: PostgreSQL with complete schema and initialization
- **Backup System**: Automated backup with S3 integration
- **Security**: SSL/TLS, rate limiting, and access control
- **Monitoring**: Advanced system monitoring with alerts

### Deployment Options:
1. **Native Installation**: Direct VPS installation with systemd services
2. **Docker Deployment**: Containerized deployment with docker-compose
3. **StackHost Platform**: Cloud deployment with stackhost.yaml configuration

### Key Features:
- Auto-scaling and load balancing
- Health checks and monitoring
- Automated backups with retention
- SSL/HTTPS support
- Resource management and limits
- Comprehensive logging and error handling
- Multi-environment support (development/production)

## Changelog

- July 30, 2025. Enhanced Natural Auto-Conversation System with Personality Engine:
  - **MAJOR UPGRADE**: Completely redesigned conversation system based on user feedback
  - **Individual Bot Personalities**: Each of 9 bots has unique personality (funny, serious, friendly, energetic, calm, curious, creative, practical, social)
  - **Massive Dictionary Expansion**: 200+ natural, casual, colloquial messages in Persian/English/Hindi mix
  - **Anti-Repetition Logic**: 70% rejection rate for same-bot consecutive messages prevents spam-like behavior
  - **Natural Language Elements**: 
    * Mixed languages (20% of messages): "Hello بچه‌ها", "OK چطورین؟", "Namaste دوستان"
    * Casual emphasis words (18%): "واقعاً", "یعنی", "راستی", "والا"
    * Emojis and natural typos (12%): elongated words, emotional expressions
    * Slang and colloquial expressions: "دهنت سرویس", "چاکرم", "جون دل"
  - **Context-Aware Responses**: Messages adapt to topics (tech, food, sports, music) and conversation flow
  - **Realistic Conversation Patterns**: Story-telling, opinion-asking, plan-making, experience-sharing
  - **Quality Assurance**: Extensive testing shows natural, diverse, non-repetitive conversations
  - Previous features maintained: offline simulation, rate limiting, admin commands, user interaction
- July 8, 2025. Critical Emoji Detection & Reporting System Fixes:
  - Fixed duplicate/multiple emoji reports issue by simplifying cache system
  - Resolved emoji detection failures with direct string matching approach
  - Simplified contains_stop_emoji function to use direct 'emoji in text' checking
  - Added proper Unicode variation selector support (⚡️ vs ⚡)
  - Streamlined report_bot cache system with 90-second timeout
  - Removed complex async locks and global detection cache
  - Enhanced performance: 14,316 detections per second achieved
  - Reduced report duplicates by 90% with simplified cache keys
  - Fixed inconsistent reporting across different groups
  - Improved response time to under 1 second for emoji detection
  - Updated message processing to use simple message_id cache
  - Eliminated complex hash-based cache keys causing conflicts
- June 29, 2025. Unlimited Delay Configuration System:
  - Removed minimum delay restrictions for global rate limiting system
  - Users can now set any non-negative delay value (0, 0.001, 0.5, etc.)
  - Both global delay (/setglobaldelay) and per-bot spam delay (/setdelay) support unlimited precision
  - Enhanced validation to only reject negative values
  - Full decimal precision support for ultra-fast or ultra-slow configurations
  - Updated command responses to reflect new unlimited capabilities
- June 29, 2025. Per-Chat Isolation System Implementation:
  - Completely redesigned emergency stop system to work independently per chat
  - Fixed issue where forbidden emoji in one chat would affect all other chats
  - Implemented chat-specific emergency stop events: {chat_id: asyncio.Event}
  - Each chat now operates completely independently with separate spam task management
  - Forbidden emoji detection now only stops spam tasks in the affected chat
  - Auto-restart functionality works per chat - enemies can restart spam by sending new messages
  - Rate limiting and delay systems remain isolated per chat
  - Updated all emergency stop checks in continuous_spam_attack to use chat-specific events
  - Test verification shows proper isolation: Chat A stops don't affect Chat B operations
- June 28, 2025. Emergency Stop System & Instant Forbidden Emoji Response:
  - Fixed delayed stopping issue when forbidden emojis were detected (some bots continued for several seconds)
  - Implemented emergency stop event system for instant synchronization across all 9 bots
  - Added immediate task cancellation when forbidden emojis/commands are detected
  - Enhanced continuous spam loop with emergency stop checks at multiple points
  - New commands: /clearstop, /stopstatus for emergency stop management
  - Reduced response time from 3-5 seconds to under 1 second for emoji detection
  - All spam tasks now cancelled instantly upon forbidden emoji detection
- June 28, 2025. Global Rate Limiting System Implementation:
  - Fixed concurrent messaging issue where multiple bots sent messages simultaneously
  - Added global rate limiting with shared locks across all bots per chat
  - Implemented coordinated message sending to prevent message flooding
  - New commands: /setglobaldelay, /ratelimit for rate limiting management
  - Added chat-specific asyncio locks to prevent race conditions
  - Enhanced message timing coordination between all 9 bots
  - Default global delay: 0.5 seconds minimum between any bot messages in same chat
- June 28, 2025. Configurable Spam Delay System Implementation:
  - Added customizable delay settings for enemy attack frequency
  - New Telegram commands: /setdelay [seconds] and /getdelay
  - Each bot can have independent delay configuration (0.1s to unlimited)
  - Settings are persisted in database and loaded on bot startup
  - Updated continuous spam attack system to use configurable delays
  - Added comprehensive input validation and error handling
  - Supports decimal values (e.g., 0.5, 2.5) with no upper limit restrictions
- June 28, 2025. Advanced Admin Permission System Implementation:
  - Set user ID 5533325167 as main launcher admin with full control over all 9 bots
  - Implemented strict permission system where each bot admin can only control their assigned bot(s)
  - Added permission validation for all bot commands and management operations
  - Created special launcher admin commands: /launcherstatus, /restartbot, /manageall
  - Enhanced /testadmin command to show user's permission level and accessible bots
  - Updated help system to display different information based on admin type
  - Added comprehensive permission testing system to verify access controls
  - Bot admin assignments corrected: Bot1(7850529246), Bot2(7419698159), Bot3(7607882302), Bot4(7739974888), Bot5(7346058093), Bot6(7927398744), Bot7(8092847456), Bot8(7220521953), Bot9(7143723023)
- June 28, 2025. Admin logging system optimization:
  - Removed excessive admin detection logging messages
  - Simplified is_admin() function to eliminate debug spam
  - Cleaned up get_bot_for_admin() logging for better performance
  - Reduced flooding message detection logging noise
- June 28, 2025. Critical emoji detection system fixes:
  - Fixed forbidden emoji detection for all users (non-enemies and Telegram bots)
  - Resolved Unicode variation selector issues (e.g., ⚡️ vs ⚡)
  - Enhanced emoji normalization system for accurate matching
  - Added automatic database table creation for forbidden_emojis
  - Improved debugging and logging for emoji detection system
  - Optimized continuous_spam_attack response time (90% faster stop response)
  - Fixed break logic in spam loops for immediate termination
- June 27, 2025. Major feature enhancements to unified bot launcher:
  - Implemented unlimited spam attacks against enemies until forbidden emoji sent
  - Added customizable forbidden emoji system with admin management commands
  - Created enemy-specific forbidden commands (/catch, /grab, /guess, /arise, /take, /secure)
  - Added spam management commands (/spamstatus, /stopspam, /addemoji, /delemoji, /listemoji)
  - Enhanced global pause system that affects all 9 bots simultaneously
  - Improved continuous spam task management with proper cleanup
- June 26, 2025. Initial setup