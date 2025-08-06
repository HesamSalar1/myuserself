#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test of Enhanced Security System
"""

import sys
import os
import sqlite3
import time

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_bot_launcher import UnifiedBotLauncher

def test_quick_system():
    print("🚀 Quick Enhanced Security System Test")
    print("="*50)
    
    # Create launcher instance
    launcher = UnifiedBotLauncher()
    
    # Setup basic configuration
    launcher.forbidden_emojis = set()
    launcher.forbidden_words = set()
    launcher.bot_configs = {1: {'db_path': 'test_quick.db'}}
    
    # Setup security settings
    launcher.security_settings = {
        'emoji_detection_enabled': True,
        'word_detection_enabled': True,
        'log_detections': True
    }
    
    # Initialize database
    launcher.setup_database(1, 'test_quick.db')
    
    print("✅ System initialized")
    
    # Test 1: Add emojis manually to memory
    test_emojis = ['⚡', '🔮', '💎']
    for emoji in test_emojis:
        launcher.forbidden_emojis.add(emoji)
    print(f"✅ Added {len(test_emojis)} test emojis to memory")
    
    # Test 2: Add words manually to memory  
    test_words = ['CHARACTER', 'test', 'spawned']
    for word in test_words:
        launcher.forbidden_words.add(word)
    print(f"✅ Added {len(test_words)} test words to memory")
    
    # Test 3: Test emoji detection
    test_text_emoji = "A CHARACTER HAS SPAWNED ⚡"
    found_emojis = []
    emoji_detected = launcher.contains_stop_emoji(test_text_emoji, found_emojis)
    print(f"🔍 Emoji test: '{test_text_emoji[:30]}...'")
    print(f"   Result: {emoji_detected}, Found: {found_emojis}")
    
    # Test 4: Test word detection
    test_text_word = "A CHARACTER HAS SPAWNED"
    found_words = []
    word_detected = launcher.contains_forbidden_word(test_text_word, found_words)
    print(f"🔍 Word test: '{test_text_word}'")
    print(f"   Result: {word_detected}, Found: {found_words}")
    
    # Test 5: Test comprehensive check
    comprehensive_issues = launcher.comprehensive_security_check(
        test_text_emoji, 12345, 'TestUser', -1001, 'TestChat', 1
    )
    print(f"🛡️ Comprehensive test: {len(comprehensive_issues)} issues found")
    for issue in comprehensive_issues:
        print(f"   - {issue['type']}: {issue['content']}")
    
    # Test 6: Performance test
    start_time = time.time()
    for i in range(100):
        launcher.contains_stop_emoji(test_text_emoji)
        launcher.contains_forbidden_word(test_text_word)
    end_time = time.time()
    avg_time = ((end_time - start_time) / 200) * 1000
    print(f"⚡ Performance: {avg_time:.2f}ms average per detection")
    
    print("\n🎯 Summary:")
    print(f"   Emojis in memory: {len(launcher.forbidden_emojis)}")
    print(f"   Words in memory: {len(launcher.forbidden_words)}")
    print(f"   Emoji detection: {'✅ Working' if emoji_detected else '❌ Failed'}")
    print(f"   Word detection: {'✅ Working' if word_detected else '❌ Failed'}")
    print(f"   Comprehensive: {'✅ Working' if comprehensive_issues else '❌ Failed'}")
    
    # Cleanup
    if os.path.exists('test_quick.db'):
        os.remove('test_quick.db')
    
    total_working = sum([emoji_detected, word_detected, bool(comprehensive_issues)])
    print(f"\n🏆 Overall: {total_working}/3 systems working ({'✅ GOOD' if total_working >= 2 else '❌ NEEDS FIX'})")

if __name__ == "__main__":
    test_quick_system()