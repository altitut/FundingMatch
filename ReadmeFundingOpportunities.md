# Funding Opportunities Management Guide

## Overview

This guide provides instructions for managing NSF funding opportunities data, including how to update, add, and remove opportunities using the comprehensive funding analysis system.

## File Structure

```
FundingOpportunities/
├── Ingested/                              # Processed CSV files with timestamps
├── nsf_funding_semantic.json              # Enhanced opportunities with AI analysis
└── ReadmeFundingOpportunities.md          # This file
```

## How to Update Funding Opportunities

### Method 1: Adding New CSV Files

1. **Place new CSV files** in the `FundingOpportunities/` folder
2. **Run the analysis script**:
   ```bash
   python comprehensive_funding_analysis.py
   ```
3. **Script will automatically**:
   - Discover and process all CSV files
   - Enhance opportunities with AI analysis
   - Move processed files to `Ingested/` folder with timestamps
   - Generate updated `nsf_funding_semantic.json`

### Method 2: Force Reprocessing

To reprocess all opportunities (useful when you want to refresh analysis):

```bash
python comprehensive_funding_analysis.py --force
```

## How to Add New Opportunities

1. **Add new rows** to existing CSV files in `FundingOpportunities/` folder
2. **Ensure CSV headers match** the existing structure:
   - Required fields vary by source (NSF, SBIR, etc.)
   - Common fields: Title, Description, Agency, Program, etc.
3. **Run the processing script**:
   ```bash
   python comprehensive_funding_analysis.py
   ```
4. **New opportunities will be**:
   - Automatically detected and processed
   - Enhanced with AI semantic analysis
   - Integrated into the output file

## How to Remove Outdated Opportunities

### Method 1: Source File Modification (Recommended)

1. **Remove rows** from CSV files in `FundingOpportunities/` folder
2. **Run script with --force** to reprocess all:
   ```bash
   python comprehensive_funding_analysis.py --force
   ```

### Method 2: Manual JSON Editing (Advanced)

1. **Backup the file** before making changes:
   ```bash
   cp FundingOpportunities/nsf_funding_semantic.json FundingOpportunities/nsf_funding_semantic_backup.json
   ```
2. **Edit the JSON file** to remove specific opportunities
3. **Update metadata counters** in the file:
   - `total_enhanced_opportunities`
   - `successful_analyses`
   - `total_opportunities`

⚠️ **Warning**: Manual edits may be overwritten when the script runs again.

## Command Line Options

| Command | Description |
|---------|-------------|
| `python comprehensive_funding_analysis.py` | Process all CSV files completely |
| `python comprehensive_funding_analysis.py --quick` | Process first 5 opportunities (testing) |
| `python comprehensive_funding_analysis.py --test` | Process 82 opportunities from each file |
| `python comprehensive_funding_analysis.py --force` | Force reprocess all data |

## Testing and Validation

### Quick Test (5 opportunities)
```bash
python comprehensive_funding_analysis.py --quick
```

### Medium Test (82 opportunities per file)
```bash
python comprehensive_funding_analysis.py --test
```

### Full Processing
```bash
python comprehensive_funding_analysis.py
```

## Data Quality Guidelines

1. **CSV Format Requirements**:
   - UTF-8 encoding
   - Proper header row
   - Consistent column names
   - No empty header cells

2. **Required Fields** (varies by source):
   - Title or Topic Title
   - Description or Synopsis
   - Program/Agency information
   - Dates (if available)

3. **Optional but Recommended**:
   - Program URLs
   - Solicitation URLs
   - Keywords
   - Contact information

## Output File Structure

The generated `nsf_funding_semantic.json` follows this structure:

```json
{
  "nsf_funding_opportunities_semantic": {
    "metadata": {
      "processing_timestamp": "...",
      "source_files": [...],
      "semantic_enhancement": {...}
    },
    "opportunities": [
      {
        "original_fields": "...",
        "semantic_analysis": {
          "enhanced_description": "...",
          "technical_focus_areas": [...],
          "strategic_context": "...",
          "semantic_keywords": [...],
          "match_ready_summary": "..."
        }
      }
    ]
  }
}
```

## Integration with Matching System

The output file is designed to work with `nsf_comprehensive_matcher.py`:

1. **Maintains compatibility** with existing matching algorithms
2. **Preserves original data** while adding semantic enhancements
3. **Structured for efficient** researcher-opportunity matching

## Maintenance Notes

- **Backup important data** before major changes
- **Check processing reports** (`NSF_semantic_report.md`) for errors
- **Monitor `Ingested/` folder** for processed file history
- **Review semantic enhancement** success rates in metadata

## Troubleshooting

### Common Issues

1. **"No CSV files found"**: Ensure CSV files are in root of `FundingOpportunities/` folder
2. **"GEMINI_API_KEY not found"**: Check `.env` file has valid API key
3. **Processing errors**: Check `NSF_semantic_report.md` for detailed error analysis

### Getting Help

1. Review processing reports for detailed statistics
2. Check log output for specific error messages
3. Verify CSV file format and encoding
4. Ensure proper API key configuration

---

**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}  
**System Version**: Comprehensive Funding Analysis v1.0
