#!/usr/bin/env python3
"""
Translation Management Script for Dreame Mower Integration

This script uses Google Translate to automatically generate and update translation files
for the Home Assistant integration, keeping all languages in sync with the English master.

Key features:
- Automatically synchronizes translation file structure with en.json
- Removes obsolete keys that no longer exist in the English master
- Only translates missing keys (preserves existing translations)
- Force mode to retranslate all keys
- Quiet by default with optional verbose output

Requirements:
    .venv/bin/pip install googletrans==4.0.0rc1

Usage:
    # Translate all languages (quiet by default)
    .venv/bin/python dev/translate_strings.py

    # Translate specific languages
    .venv/bin/python dev/translate_strings.py --languages de fr es

    # Show verbose output (including "Keeping existing" messages)
    .venv/bin/python dev/translate_strings.py --verbose

    # Dry run (preview translations without writing files)
    .venv/bin/python dev/translate_strings.py --dry-run

    # Force retranslate all strings (not just missing ones)
    .venv/bin/python dev/translate_strings.py --force

Languages supported:
    de (German), fr (French), es (Spanish), it (Italian), 
    pt (Portuguese), pt-BR (Brazilian Portuguese), sv (Swedish), 
    nl (Dutch), hu (Hungarian), pl (Polish), ru (Russian), uk (Ukrainian)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio

try:
    from googletrans import Translator  # type: ignore[import-not-found]
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False
    print("❌ Error: googletrans library not found.")
    print("Install it with: .venv/bin/pip install googletrans")
    sys.exit(1)

# Language configurations
LANGUAGES = {
    'de': 'German',
    'fr': 'French', 
    'es': 'Spanish',
    'it': 'Italian',
    'pt': 'Portuguese',
    'pt-BR': 'Portuguese (Brazil)',
    'sv': 'Swedish',
    'nl': 'Dutch',
    'hu': 'Hungarian',
    'pl': 'Polish',
    'ru': 'Russian',
    'uk': 'Ukrainian'
}

# Map Google Translate language codes
TRANSLATE_LANG_MAP = {
    'pt-BR': 'pt',  # Google Translate uses 'pt' for Portuguese
}

class TranslationManager:
    def __init__(self, dry_run: bool = False, force: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.force = force
        self.verbose = verbose
        self.translator = Translator()
        self.translations_dir = Path(__file__).parent.parent / 'custom_components' / 'dreame_mower' / 'translations'
        self.english_file = self.translations_dir / 'en.json'
        
        if not self.english_file.exists():
            raise FileNotFoundError(f"English master file not found: {self.english_file}")
    
    def load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"⚠️  Warning: Could not load {file_path}: {e}")
            return {}
    
    def save_json(self, data: Dict[str, Any], file_path: Path) -> None:
        """Save JSON file with proper formatting."""
        if self.dry_run:
            print(f"🔍 [DRY RUN] Would save to: {file_path}")
            return
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved: {file_path}")
    
    async def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text using Google Translate asynchronously."""
        if not text or text.strip() == "":
            return text
        
        # Map language codes for Google Translate
        google_lang = TRANSLATE_LANG_MAP.get(target_lang, target_lang)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add small delay to avoid rate limiting
                if attempt > 0:
                    await asyncio.sleep(1)
                
                result = await self.translator.translate(text, src='en', dest=google_lang)
                if result and hasattr(result, 'text') and result.text:
                    return result.text
                else:
                    print(f"⚠️  Warning: Empty translation result for '{text}' -> {target_lang}")
                    return text
                    
            except Exception as e:
                print(f"⚠️  Translation attempt {attempt + 1} failed for '{text}' -> {target_lang}: {e}")
                if attempt == max_retries - 1:
                    print(f"❌ Failed to translate '{text}' after {max_retries} attempts, keeping original")
                    return text
                await asyncio.sleep(2)  # Wait longer between retries
        
        return text
    
    async def translate_dict_recursive(self, data: Dict[str, Any], target_lang: str, existing_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Recursively translate dictionary values asynchronously."""
        if existing_data is None:
            existing_data = {}
        
        result: Dict[str, Any] = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursive translation for nested dictionaries
                existing_nested = existing_data.get(key, {}) if isinstance(existing_data.get(key), dict) else {}
                result[key] = await self.translate_dict_recursive(value, target_lang, existing_nested)
            elif isinstance(value, str):
                # Check if translation already exists and force flag
                if not self.force and key in existing_data and isinstance(existing_data[key], str) and existing_data[key].strip():
                    result[key] = existing_data[key]  # Keep existing translation
                    if self.verbose:
                        print(f"📋 Keeping existing: {key} = '{existing_data[key]}'")
                else:
                    # Translate the string
                    translated = await self.translate_text(value, target_lang)
                    result[key] = translated
                    print(f"🔄 Translated ({target_lang}): {key} = '{value}' -> '{translated}'")
            else:
                # Non-string values (arrays, numbers, etc.) - copy as is
                result[key] = value
        
        return result

    def _find_removed_keys(self, english_data: Dict[str, Any], existing_data: Dict[str, Any], path: str = "") -> List[str]:
        """Find keys that exist in existing_data but not in english_data."""
        removed_keys = []
        
        for key, value in existing_data.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in english_data:
                # Key was completely removed
                removed_keys.append(current_path)
            elif isinstance(value, dict) and isinstance(english_data.get(key), dict):
                # Recursively check nested dictionaries
                removed_keys.extend(
                    self._find_removed_keys(english_data[key], value, current_path)
                )
            elif isinstance(value, dict) and not isinstance(english_data.get(key), dict):
                # Structure changed - nested dict was replaced with non-dict
                removed_keys.append(current_path)
                
        return removed_keys
    
    async def translate_language(self, lang_code: str) -> None:
        """Translate to a specific language asynchronously."""
        print(f"\n🌍 Translating to {LANGUAGES[lang_code]} ({lang_code})...")
        
        # Load English master
        english_data = self.load_json(self.english_file)
        if not english_data:
            print(f"❌ Could not load English master file")
            return
        
        # Load existing translation if it exists
        target_file = self.translations_dir / f'{lang_code}.json'
        existing_data = self.load_json(target_file) if target_file.exists() else {}
        
        # Find and report removed keys
        if existing_data:
            removed_keys = self._find_removed_keys(english_data, existing_data)
            if removed_keys:
                print(f"🗑️  Removing {len(removed_keys)} obsolete keys: {', '.join(removed_keys)}")
        
        # Translate (this will only include keys present in english_data)
        translated_data = await self.translate_dict_recursive(english_data, lang_code, existing_data)
        
        # Save result
        self.save_json(translated_data, target_file)
        print(f"✅ Completed translation for {LANGUAGES[lang_code]}")
    
    async def translate_all(self, languages: Optional[List[str]] = None) -> None:
        """Translate to all or specified languages asynchronously."""
        target_languages = languages if languages else list(LANGUAGES.keys())
        
        print(f"🚀 Starting async translation for languages: {', '.join(target_languages)}")
        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")
        if self.force:
            print("🔄 FORCE MODE - All strings will be retranslated")
        
        for lang_code in target_languages:
            if lang_code not in LANGUAGES:
                print(f"⚠️  Warning: Unknown language code '{lang_code}', skipping")
                continue
            
            try:
                await self.translate_language(lang_code)
            except Exception as e:
                print(f"❌ Error translating to {lang_code}: {e}")
                continue
        
        print(f"\n🎉 Translation completed for {len(target_languages)} languages!")


async def main():
    parser = argparse.ArgumentParser(
        description="Translate Dreame Mower integration strings using Google Translate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--languages', '-l',
        nargs='+',
        help='Specific language codes to translate (default: all)',
        choices=list(LANGUAGES.keys())
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview translations without writing files'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force retranslate all strings (not just missing ones)'
    )
    parser.add_argument(
        '--list-languages',
        action='store_true',
        help='List all supported language codes'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose output (including "Keeping existing" messages)'
    )
    
    args = parser.parse_args()
    
    if args.list_languages:
        print("Supported languages:")
        for code, name in LANGUAGES.items():
            print(f"  {code:6} - {name}")
        return
    
    if not HAS_GOOGLETRANS:
        return
    
    try:
        manager = TranslationManager(dry_run=args.dry_run, force=args.force, verbose=args.verbose)
        await manager.translate_all(args.languages)
    except KeyboardInterrupt:
        print("\n⏹️  Translation interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


def run_main():
    """Wrapper to run the async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Translation interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    run_main()