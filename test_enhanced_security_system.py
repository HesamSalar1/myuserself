#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Security System Test
Test comprehensive forbidden emoji and word detection system
"""

import asyncio
import sqlite3
import time
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_bot_launcher import UnifiedBotLauncher

class EnhancedSecurityTester:
    def __init__(self):
        self.launcher = UnifiedBotLauncher()
        self.test_results = {
            'emoji_tests': [],
            'word_tests': [],
            'integration_tests': [],
            'performance_tests': []
        }
        self.setup_test_environment()

    def setup_test_environment(self):
        """Initialize test environment"""
        print("🔧 Setting up enhanced security test environment...")
        
        # Initialize the launcher with proper configuration
        self.launcher.forbidden_emojis = set()
        self.launcher.forbidden_words = set()
        self.launcher.security_settings = {
            'emoji_detection_enabled': True,
            'word_detection_enabled': True,
            'log_detections': True,
            'case_sensitive_words': False,
            'partial_word_matching': True
        }
        self.launcher.security_stats = {
            'emoji_detections': 0,
            'word_detections': 0
        }
        self.launcher.detection_cache = {}
        self.launcher.cache_max_size = 100
        self.launcher.cache_expiry = 60
        
        # Setup bot configurations for database access
        self.launcher.bot_configs = {
            1: {
                'db_path': 'test_bot_data.db',
                'api_id': 'test',
                'api_hash': 'test',
                'session_name': 'test'
            }
        }
        
        # Initialize the database for testing
        self.launcher.setup_database(1, 'test_bot_data.db')
        
        print("✅ Test environment ready")

    def test_emoji_management(self):
        """Test enhanced emoji management functions"""
        print("\n🚫 Testing Enhanced Emoji Management...")
        
        test_cases = [
            {'emoji': '⚡', 'description': 'Lightning bolt', 'category': 'gaming'},
            {'emoji': '🔮', 'description': 'Crystal ball', 'category': 'magic'},
            {'emoji': '💎', 'description': 'Diamond', 'category': 'treasure'},
            {'emoji': '⚡️', 'description': 'Lightning with variation', 'category': 'gaming'},
        ]
        
        for case in test_cases:
            try:
                # Test adding emoji
                result = self.launcher.add_forbidden_emoji_advanced(
                    case['emoji'], 
                    case['description'], 
                    case['category'], 
                    added_by_user_id=12345
                )
                
                self.test_results['emoji_tests'].append({
                    'test': f"Add emoji {case['emoji']}",
                    'result': 'PASS' if result else 'FAIL',
                    'details': case
                })
                
                if result:
                    print(f"  ✅ Added: {case['emoji']} ({case['description']})")
                else:
                    print(f"  ❌ Failed to add: {case['emoji']}")
                    
            except Exception as e:
                print(f"  ❌ Error adding {case['emoji']}: {e}")
                self.test_results['emoji_tests'].append({
                    'test': f"Add emoji {case['emoji']}",
                    'result': 'ERROR',
                    'details': str(e)
                })

    def test_word_management(self):
        """Test enhanced word management functions"""
        print("\n📝 Testing Enhanced Word Management...")
        
        test_cases = [
            {
                'word': 'CHARACTER', 
                'description': 'Game character spawn',
                'case_sensitive': True,
                'partial_match': False
            },
            {
                'word': 'test', 
                'description': 'Test word partial',
                'case_sensitive': False,
                'partial_match': True
            },
            {
                'word': 'spawned', 
                'description': 'Something spawned',
                'case_sensitive': False,
                'partial_match': True
            },
            {
                'word': 'EXACT', 
                'description': 'Exact case match',
                'case_sensitive': True,
                'partial_match': False
            }
        ]
        
        for case in test_cases:
            try:
                # Test adding word
                result = self.launcher.add_forbidden_word_advanced(
                    case['word'],
                    case['description'],
                    'test_category',
                    case_sensitive=case['case_sensitive'],
                    partial_match=case['partial_match'],
                    added_by_user_id=12345
                )
                
                match_type = "exact" if not case['partial_match'] else "partial"
                case_type = "sensitive" if case['case_sensitive'] else "insensitive"
                
                self.test_results['word_tests'].append({
                    'test': f"Add word '{case['word']}' ({match_type}, {case_type})",
                    'result': 'PASS' if result else 'FAIL',
                    'details': case
                })
                
                if result:
                    print(f"  ✅ Added: '{case['word']}' ({match_type}, {case_type})")
                else:
                    print(f"  ❌ Failed to add: '{case['word']}'")
                    
            except Exception as e:
                print(f"  ❌ Error adding '{case['word']}': {e}")
                self.test_results['word_tests'].append({
                    'test': f"Add word '{case['word']}'",
                    'result': 'ERROR',
                    'details': str(e)
                })

    def test_detection_system(self):
        """Test the enhanced detection system"""
        print("\n🔍 Testing Enhanced Detection System...")
        
        # Test emoji detection
        emoji_test_cases = [
            {'text': '⚡ lightning test', 'should_detect': True, 'expected': '⚡'},
            {'text': '⚡️ lightning with variation', 'should_detect': True, 'expected': '⚡'},
            {'text': 'A CHARACTER HAS SPAWNED ⚡', 'should_detect': True, 'expected': '⚡'},
            {'text': '🔮 crystal ball', 'should_detect': True, 'expected': '🔮'},
            {'text': 'normal text without emojis', 'should_detect': False, 'expected': None},
            {'text': '💎 diamond gem', 'should_detect': True, 'expected': '💎'},
        ]
        
        print("  🚫 Emoji Detection Tests:")
        for i, case in enumerate(emoji_test_cases, 1):
            try:
                start_time = time.time()
                found_emojis = []
                detected = self.launcher.contains_stop_emoji(case['text'], found_emojis)
                end_time = time.time()
                detection_time = (end_time - start_time) * 1000
                
                success = detected == case['should_detect']
                if detected and found_emojis:
                    success = success and (found_emojis[0] == case['expected'])
                
                result = 'PASS' if success else 'FAIL'
                status = '✅' if success else '❌'
                
                print(f"    {i}. {status} '{case['text'][:30]}...' → {detected} ({detection_time:.2f}ms)")
                if detected and found_emojis:
                    print(f"       Found: {found_emojis[0]}")
                
                self.test_results['emoji_tests'].append({
                    'test': f"Detect emoji in: {case['text'][:20]}...",
                    'result': result,
                    'time_ms': detection_time,
                    'details': {
                        'expected': case['should_detect'],
                        'actual': detected,
                        'found': found_emojis[0] if found_emojis else None
                    }
                })
                
            except Exception as e:
                print(f"    {i}. ❌ Error: {e}")
                self.test_results['emoji_tests'].append({
                    'test': f"Detect emoji in: {case['text'][:20]}...",
                    'result': 'ERROR',
                    'details': str(e)
                })

        # Test word detection
        word_test_cases = [
            {'text': 'A CHARACTER HAS SPAWNED', 'should_detect': True, 'expected': 'CHARACTER'},
            {'text': 'a character has spawned', 'should_detect': True, 'expected': 'CHARACTER'},
            {'text': 'This is a test message', 'should_detect': True, 'expected': 'test'},
            {'text': 'Something spawned here', 'should_detect': True, 'expected': 'spawned'},
            {'text': 'EXACT word test', 'should_detect': True, 'expected': 'EXACT'},
            {'text': 'exact word test', 'should_detect': False, 'expected': None},  # case sensitive
            {'text': 'normal message', 'should_detect': False, 'expected': None},
        ]
        
        print("\n  📝 Word Detection Tests:")
        for i, case in enumerate(word_test_cases, 1):
            try:
                start_time = time.time()
                found_words = []
                detected = self.launcher.contains_forbidden_word(case['text'], found_words)
                end_time = time.time()
                detection_time = (end_time - start_time) * 1000
                
                success = detected == case['should_detect']
                if detected and found_words and case['expected']:
                    success = success and (case['expected'].lower() in found_words[0].lower())
                
                result = 'PASS' if success else 'FAIL'
                status = '✅' if success else '❌'
                
                print(f"    {i}. {status} '{case['text']}' → {detected} ({detection_time:.2f}ms)")
                if detected and found_words:
                    print(f"       Found: {found_words[0]}")
                
                self.test_results['word_tests'].append({
                    'test': f"Detect word in: {case['text']}",
                    'result': result,
                    'time_ms': detection_time,
                    'details': {
                        'expected': case['should_detect'],
                        'actual': detected,
                        'found': found_words[0] if found_words else None
                    }
                })
                
            except Exception as e:
                print(f"    {i}. ❌ Error: {e}")
                self.test_results['word_tests'].append({
                    'test': f"Detect word in: {case['text']}",
                    'result': 'ERROR',
                    'details': str(e)
                })

    def test_comprehensive_security_check(self):
        """Test the comprehensive security check function"""
        print("\n🛡️ Testing Comprehensive Security Check...")
        
        test_cases = [
            {
                'text': 'A CHARACTER HAS SPAWNED ⚡',
                'expected_emoji': '⚡',
                'expected_word': 'CHARACTER',
                'description': 'Both emoji and word detection'
            },
            {
                'text': 'This is a test message with 🔮',
                'expected_emoji': '🔮',
                'expected_word': 'test',
                'description': 'Multiple detections'
            },
            {
                'text': 'Normal message without issues',
                'expected_emoji': None,
                'expected_word': None,
                'description': 'Clean message'
            },
            {
                'text': 'Something spawned but no emoji',
                'expected_emoji': None,
                'expected_word': 'spawned',
                'description': 'Word only detection'
            },
            {
                'text': 'Just emoji 💎 here',
                'expected_emoji': '💎',
                'expected_word': None,
                'description': 'Emoji only detection'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            try:
                start_time = time.time()
                detected_issues = self.launcher.comprehensive_security_check(
                    case['text'], 12345, 'TestUser', -1001234567890, 'Test Group', 1
                )
                end_time = time.time()
                detection_time = (end_time - start_time) * 1000
                
                # Analyze results
                emoji_detected = any(issue['type'] == 'forbidden_emoji' for issue in detected_issues)
                word_detected = any(issue['type'] == 'forbidden_word' for issue in detected_issues)
                
                emoji_content = None
                word_content = None
                for issue in detected_issues:
                    if issue['type'] == 'forbidden_emoji':
                        emoji_content = issue['content']
                    elif issue['type'] == 'forbidden_word':
                        word_content = issue['content']
                
                # Check success
                emoji_success = (emoji_detected and case['expected_emoji']) or (not emoji_detected and not case['expected_emoji'])
                word_success = (word_detected and case['expected_word']) or (not word_detected and not case['expected_word'])
                success = emoji_success and word_success
                
                result = 'PASS' if success else 'FAIL'
                status = '✅' if success else '❌'
                
                print(f"  {i}. {status} {case['description']} ({detection_time:.2f}ms)")
                print(f"     Text: '{case['text']}'")
                print(f"     Issues found: {len(detected_issues)}")
                if detected_issues:
                    for issue in detected_issues:
                        print(f"     - {issue['type']}: {issue['content']}")
                
                self.test_results['integration_tests'].append({
                    'test': case['description'],
                    'result': result,
                    'time_ms': detection_time,
                    'details': {
                        'expected_emoji': case['expected_emoji'],
                        'expected_word': case['expected_word'],
                        'found_emoji': emoji_content,
                        'found_word': word_content,
                        'total_issues': len(detected_issues)
                    }
                })
                
            except Exception as e:
                print(f"  {i}. ❌ Error in comprehensive check: {e}")
                self.test_results['integration_tests'].append({
                    'test': case['description'],
                    'result': 'ERROR',
                    'details': str(e)
                })

    def test_performance(self):
        """Test performance of the detection system"""
        print("\n⚡ Testing Performance...")
        
        # Performance test cases
        test_texts = [
            "A CHARACTER HAS SPAWNED ⚡",
            "🔮 This is a test message with crystal ball",
            "Something spawned here with 💎 diamond",
            "Normal message without any issues",
            "EXACT word test with ⚡️ lightning",
        ] * 20  # 100 total tests
        
        print(f"  Running {len(test_texts)} detection tests...")
        
        # Emoji performance test
        start_time = time.time()
        emoji_detections = 0
        for text in test_texts:
            if self.launcher.contains_stop_emoji(text):
                emoji_detections += 1
        emoji_time = time.time() - start_time
        
        # Word performance test
        start_time = time.time()
        word_detections = 0
        for text in test_texts:
            if self.launcher.contains_forbidden_word(text):
                word_detections += 1
        word_time = time.time() - start_time
        
        # Comprehensive test
        start_time = time.time()
        comprehensive_detections = 0
        for text in test_texts:
            issues = self.launcher.comprehensive_security_check(text, 12345, 'Test', -1001, 'Test', 1)
            if issues:
                comprehensive_detections += 1
        comprehensive_time = time.time() - start_time
        
        # Calculate statistics
        emoji_avg = (emoji_time / len(test_texts)) * 1000
        word_avg = (word_time / len(test_texts)) * 1000
        comprehensive_avg = (comprehensive_time / len(test_texts)) * 1000
        
        print(f"  📊 Performance Results:")
        print(f"    Emoji Detection: {emoji_avg:.2f}ms avg, {emoji_detections} detections")
        print(f"    Word Detection: {word_avg:.2f}ms avg, {word_detections} detections")
        print(f"    Comprehensive: {comprehensive_avg:.2f}ms avg, {comprehensive_detections} detections")
        print(f"    Tests per second: {len(test_texts)/comprehensive_time:.0f}")
        
        self.test_results['performance_tests'].append({
            'test': 'Performance benchmark',
            'result': 'PASS' if comprehensive_avg < 10 else 'SLOW',
            'details': {
                'emoji_avg_ms': emoji_avg,
                'word_avg_ms': word_avg,
                'comprehensive_avg_ms': comprehensive_avg,
                'tests_per_second': len(test_texts)/comprehensive_time,
                'total_tests': len(test_texts)
            }
        })

    def test_database_operations(self):
        """Test database operations for emojis and words"""
        print("\n💾 Testing Database Operations...")
        
        try:
            # Test emoji list retrieval
            emoji_list = self.launcher.list_forbidden_emojis_advanced()
            print(f"  ✅ Retrieved {len(emoji_list)} emojis from database")
            
            # Test word list retrieval
            word_list = self.launcher.list_forbidden_words_advanced()
            print(f"  ✅ Retrieved {len(word_list)} words from database")
            
            # Test removal operations
            if emoji_list:
                test_emoji = emoji_list[0]['emoji']
                result, msg = self.launcher.remove_forbidden_emoji_advanced(test_emoji, 12345)
                print(f"  {'✅' if result else '❌'} Remove emoji test: {msg}")
            
            if word_list:
                test_word = word_list[0]['word']
                result, msg = self.launcher.remove_forbidden_word_advanced(test_word, 12345)
                print(f"  {'✅' if result else '❌'} Remove word test: {msg}")
            
        except Exception as e:
            print(f"  ❌ Database operations error: {e}")

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📋 ENHANCED SECURITY SYSTEM TEST REPORT")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            if not tests:
                continue
                
            category_total = len(tests)
            category_passed = sum(1 for test in tests if test['result'] == 'PASS')
            total_tests += category_total
            passed_tests += category_passed
            
            print(f"\n📊 {category.replace('_', ' ').title()}:")
            print(f"   ✅ Passed: {category_passed}/{category_total}")
            
            if category_passed < category_total:
                print("   ❌ Failed tests:")
                for test in tests:
                    if test['result'] != 'PASS':
                        print(f"     - {test['test']}: {test['result']}")
        
        print(f"\n🎯 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED! Enhanced security system is working perfectly.")
        else:
            print(f"\n⚠️ Some tests failed. Please review the results above.")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

async def main():
    """Run all enhanced security system tests"""
    print("🔐 ENHANCED SECURITY SYSTEM TEST SUITE")
    print("Testing comprehensive forbidden emoji and word detection")
    print("="*60)
    
    tester = EnhancedSecurityTester()
    
    try:
        # Run all tests
        tester.test_emoji_management()
        tester.test_word_management()
        tester.test_detection_system()
        tester.test_comprehensive_security_check()
        tester.test_performance()
        tester.test_database_operations()
        
        # Generate final report
        tester.generate_report()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Critical test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)