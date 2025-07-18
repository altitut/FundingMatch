# NSF Funding Opportunities Semantic Analysis Report

## Executive Summary

**Analysis Date:** 2025-07-14 16:25:32  
**Total Opportunities Processed:** 5  
**Analysis Model:** Gemini 2.5 Pro  
**Processing Mode:** Parallel Processing (Max 150 RPM)

## Processing Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Successful Analyses** | 5 | 100.0% |
| **403 Forbidden Errors** | 0 | 0.0% |
| **Analysis Errors** | 0 | 0.0% |
| **Total Processed** | 5 | 100.0% |

## Successful Analyses

### Summary
- **Total Successful:** 5
- **Average Analysis Time:** 74.6s (if any)
- **Program URLs Processed:** 5
- **Solicitation URLs Processed:** 0

### Detailed Results

| Program ID | Title | Analysis Time (s) | Program URL | Solicitation URL |
|------------|-------|-------------------|-------------|------------------|
| A25D-020 | Photonic Crystal Surface-Emitting Lasers... | 71.0 | ✅ | ❌ |
| A254-047 | Photonic Crystal Surface-Emitting Lasers... | 75.2 | ✅ | ❌ |
| SF254-01006 | Low-Cost, Expendable, Launch-Agnostic Sp... | 75.3 | ✅ | ❌ |
| SF254-D1004 | Autonomous Modular Material Handling Equ... | 75.4 | ✅ | ❌ |
| A254-046 | Underwater Sensing in Surf Zone Environm... | 75.9 | ✅ | ❌ |


## 403 Forbidden Errors

### Summary
- **Total 403 Errors:** 0
- **Impact:** These opportunities were skipped due to access restrictions on NSF URLs

### Detailed Results

*No 403 errors to report.*


## Analysis Errors

### Summary
- **Total Analysis Errors:** 0
- **Impact:** These opportunities failed during AI analysis processing

### Detailed Results

*No analysis errors to report.*


## Recommendations

### For 403 Forbidden Errors
1. **NSF URL Access:** The NSF website may be blocking automated access to certain pages
2. **Alternative Approach:** Consider using NSF's official API or RSS feeds if available
3. **Manual Review:** High-priority opportunities with 403 errors may need manual review

### For Analysis Errors
1. **Retry Logic:** Implement retry mechanisms for transient errors
2. **Input Validation:** Enhance input validation for malformed opportunity data
3. **Fallback Analysis:** Use basic analysis for opportunities that fail comprehensive analysis

### Processing Optimization
1. **Rate Limiting:** Current 150 RPM limit appears appropriate
2. **Parallel Processing:** 5 workers provided good throughput
3. **Error Handling:** Robust error handling allowed processing to continue despite individual failures

## Technical Details

- **Processing Duration:** Approximately 5.8 minutes (estimated)
- **API Calls:** ~15 total calls (analysis + URL fetching)
- **Output File:** FundingOpportunitiesManual/nsf_funding_semantic.json
- **Enhancement Features:** Enhanced descriptions, technical focus areas, semantic keywords, strategic context

---

*Report generated on 2025-07-14 16:25:32 using Gemini 2.5 Pro*
