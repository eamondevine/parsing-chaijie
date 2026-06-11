# PARSING PROJECT FOR CHAIJIE:

### This is the repo for all the parsing stuff done for my Chaijie project

## MAKEMEAHANZI_PARSER.PY

This is a script that went through the original make me a hanzi data and stripped away all IDCs. Don't need them.

## PROCESS_CHAIJIE.PY

WARNING: This may overwrite your entries from the add_variants.py script and may cause some formatting ugliness. This script goes through each object in output.json and adds a unicode decimal and a unicode hexidecimal property. Then it rearranges the order if the characters' sequences are out of whack. Outputs a log file called changes_log.txt.

## ADD_VARIANTS.PY

Sure, here's a summary you can drop into your README:

add_variants.py
Enriches output.json with additional character data and writes the result to output_with_variants.json. The original file is never overwritten.
Requires the following files in the same directory:

output.json — the source character data
Unihan_Variants.txt — from the Unicode Consortium's Unihan database
official_characters.json — from dict.variants.moe.tw, the official Taiwan Ministry of Education character set
final_radicals.txt — fallback radical lookup for characters outside the scope of the official Taiwan data

What it adds to each character entry:

unicode — the Unicode codepoint (e.g. U+5250), inserted after character
officialChar: true — added when the character is present in the official Taiwan character set
strokeNumber — taken from the official data when available, otherwise derived by counting the character's entries in the strokes array
mismatch: true — added when the official strokeNumber disagrees with the actual count of strokes in the strokes array, for manual review
radical — replaced with the value from the official Taiwan data when available, falling back to final_radicals.txt, then the existing value
traditionalVariant — array of traditional form(s) of a simplified character, sourced from Unihan
simplifiedVariant — array of simplified form(s) of a traditional character, sourced from Unihan

Additional behavior:

Self-referencing variants are filtered out (a character is never listed as its own variant)
Existing variants properties are removed if their contents are covered by the new traditionalVariant/simplifiedVariant properties, otherwise preserved
The script is safe to re-run — properties already present in an entry are never overwritten or duplicated
All original formatting is preserved: matches arrays stay inline, stroke path strings each remain on their own line, 4-space indentation throughout

## FIND_MULTI_VARIANTS.PY

Scans output_with_variants.json and identifies any characters where traditionalVariant or simplifiedVariant contains more than one entry, writing the results to multi_variants.txt.
Requires the following file in the same directory:

output_with_variants.json — the enriched output from add_variants.py

Output format in multi_variants.txt:
么 (U+4E48) traditionalVariant: ['幺', '麼', '麽']
One line per property per character. A single character can appear twice if both its traditionalVariant and simplifiedVariant each have multiple entries.
Purpose:
Multi-variant mappings are rare but exist in the Unihan data. Some may reflect legitimate historical variant relationships while others may be questionable for practical use — for example, characters that are technically related but have diverged in meaning or pronunciation in modern usage. This file makes it easy to review and manually clean up those cases in VSCode.

## FLIP_SVG_PATHS.PY

Scans and looks at all SVG strokes and flips them on their Y-axis (the original make me a hanzi data used an upside down image when rendered in the SVG so you'd have to add a scale -1 on the SVG element on your front end).

## RADICALS.TXT

This is a sequential list of Kangxi radicals, all 214 of them.

## FINAL_RADICALS.TXT

**NOTE: this is a backup radical index to catch unicode \***not**\* covered by the official characters json file** This file contains radical information provided by the unihan database from unicode points U+3400 up to U+33479. Therefore it does _not_ cover supplemental or stroke glyphs.

## OFFICIAL_CHARACTERS.JSON

This file's contents was derived from the 正字 table from the dict.variants.moe.tw website. If a character was present within their table, that character was provided as the value of the property of "officialChar". Then following that property is the "linkId", which can be tacked on to the URL *https://dict.variants.moe.edu.tw/dictView.jsp?ID=* to go to the associated entry for the character. Then the property "radical" gives the Taiwan MOE official radical for the character which is the priority for making values to radicals in the output.json file (after that the final radicals text file takes over filling in those values via the add variants python script). Finally we have the "strokeNumber" which again takes priority in labelling the stroke number in the output.json file.
